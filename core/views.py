"""
Views for core application.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
import json

from .models import (
    ApprovalWorkflow, ApprovalRequest, ApprovalLog, 
    DashboardWidget, Notification
)
from billing.models import Invoice, Quote, PurchaseOrder, Payment
from crm.models import Party


@login_required
def dashboard(request):
    """Main dashboard view."""
    company = request.user.company
    
    # Get approval statistics
    pending_approvals = ApprovalRequest.objects.filter(
        company=company,
        status='pending'
    ).count()
    
    my_approvals = ApprovalRequest.objects.filter(
        company=company,
        current_level__lte=request.user.approval_level,
        status='pending'
    ).count()
    
    # Get recent approval requests
    recent_approvals = ApprovalRequest.objects.filter(
        company=company
    ).select_related('workflow', 'created_by').order_by('-created_at')[:5]
    
    # Get approval workflow statistics
    workflow_stats = ApprovalWorkflow.objects.filter(
        company=company
    ).annotate(
        request_count=Count('approval_requests')
    ).order_by('-request_count')[:5]
    
    # Financial data calculations
    from datetime import datetime, timedelta, date
    
    # Current month data
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Monthly revenue (CA)
    monthly_ca = Invoice.objects.filter(
        company=company,
        invoice_type='sale',
        issue_date__gte=month_start,
        status='paid'
    ).aggregate(total=Sum('total_ttc'))['total'] or 0
    
    # Monthly TVA
    monthly_tva = Invoice.objects.filter(
        company=company,
        invoice_type='sale',
        issue_date__gte=month_start,
        status='paid'
    ).aggregate(total=Sum('total_tva'))['total'] or 0
    
    # Customer balance (accounts receivable): non-paid, non-cancelled sales invoices
    customer_balance = Invoice.objects.filter(
        company=company,
        invoice_type='sale'
    ).exclude(status__in=['paid', 'cancelled']).aggregate(total=Sum('total_ttc'))['total'] or 0
    
    # Supplier balance (accounts payable): non-paid, non-cancelled purchase invoices
    supplier_balance = Invoice.objects.filter(
        company=company,
        invoice_type='purchase'
    ).exclude(status__in=['paid', 'cancelled']).aggregate(total=Sum('total_ttc'))['total'] or 0
    
    # Chart data - selectable Period (month or year)
    period = (request.GET.get('period') or 'year').lower()
    chart_labels = []
    chart_values = []
    if period == 'month':
        # Current month daily revenue (paid invoices)
        start_d = month_start.date()
        # Compute first day of next month
        next_month = (month_start + timedelta(days=32)).replace(day=1).date()
        num_days = (next_month - start_d).days
        for i in range(num_days):
            day_d = start_d + timedelta(days=i)
            next_d = day_d + timedelta(days=1)
            total = Invoice.objects.filter(
                company=company,
                invoice_type='sale',
                issue_date__gte=day_d,
                issue_date__lt=next_d,
                status='paid'
            ).aggregate(total=Sum('total_ttc'))['total'] or 0
            chart_labels.append(day_d.strftime('%d/%m'))
            chart_values.append(float(total))
    else:
        # Last 12 months monthly revenue (paid invoices)
        def month_begin(d: date, offset: int) -> date:
            total = d.year * 12 + (d.month - 1) - offset
            y = total // 12
            m = total % 12 + 1
            return date(y, m, 1)
        def month_next(d: date) -> date:
            return date(d.year + (1 if d.month == 12 else 0), 1 if d.month == 12 else d.month + 1, 1)
        # Build chronological order oldest->newest
        for i in range(11, -1, -1):
            start_m = month_begin(month_start.date(), i)
            end_m = month_next(start_m)
            total = Invoice.objects.filter(
                company=company,
                invoice_type='sale',
                issue_date__gte=start_m,
                issue_date__lt=end_m,
                status='paid'
            ).aggregate(total=Sum('total_ttc'))['total'] or 0
            chart_labels.append(start_m.strftime('%b %Y'))
            chart_values.append(float(total))
    
    # Recent invoices
    recent_invoices = Invoice.objects.filter(
        company=company
    ).select_related('party').order_by('-created_at')[:5]
    
    # Unpaid invoices: any non-paid, non-cancelled sales invoice
    unpaid_invoices = Invoice.objects.filter(
        company=company,
        invoice_type='sale'
    ).exclude(status__in=['paid', 'cancelled']).select_related('party').order_by('-due_date')[:5]
    
    # Recent payments
    recent_payments = Payment.objects.filter(
        company=company
    ).select_related('party').order_by('-date', '-created_at')[:5]
    
    # Company currency
    company_currency = getattr(company, 'default_currency', 'MAD')
    
    # Build period bounds for type breakdown (sales vs purchases)
    if period == 'month':
        type_start = month_start.date()
        type_end = (month_start + timedelta(days=32)).replace(day=1).date()
    else:
        # year: last 12 full months up to next month start
        def month_begin(d: date, offset: int) -> date:
            total = d.year * 12 + (d.month - 1) - offset
            y = total // 12
            m = total % 12 + 1
            return date(y, m, 1)
        def month_next(d: date) -> date:
            return date(d.year + (1 if d.month == 12 else 0), 1 if d.month == 12 else d.month + 1, 1)
        type_start = month_begin(month_start.date(), 11)
        type_end = month_next(month_start.date())

    sales_total = Invoice.objects.filter(
        company=company,
        invoice_type='sale',
        issue_date__gte=type_start,
        issue_date__lt=type_end,
        status='paid'
    ).aggregate(total=Sum('total_ttc'))['total'] or 0
    purchase_total = Invoice.objects.filter(
        company=company,
        invoice_type='purchase',
        issue_date__gte=type_start,
        issue_date__lt=type_end,
    ).exclude(status__in=['draft', 'cancelled']).aggregate(total=Sum('total_ttc'))['total'] or 0

    # Current date for template
    now = timezone.now()
    
    context = {
        'company': company,
        'pending_approvals': pending_approvals,
        'my_approvals': my_approvals,
        'recent_approvals': recent_approvals,
        'workflow_stats': workflow_stats,
        'monthly_ca': monthly_ca,
        'monthly_tva': monthly_tva,
        'customer_balance': customer_balance,
        'supplier_balance': supplier_balance,
        'month_start': month_start,
        'company_currency': company_currency,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'period': period,
        'recent_invoices': recent_invoices,
        'unpaid_invoices': unpaid_invoices,
        'recent_payments': recent_payments,
        'now': now,
        'sales_total': float(sales_total or 0),
        'purchase_total': float(purchase_total or 0),
    }
    
    return render(request, 'core/dashboard.html', context)


# Approval Workflow Views
@login_required
def workflow_list(request):
    """List all approval workflows."""
    company = request.user.company
    
    workflows = ApprovalWorkflow.objects.filter(company=company).annotate(
        request_count=Count('approval_requests'),
        active_requests=Count('approval_requests', filter=Q(approval_requests__status='pending'))
    ).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        workflows = workflows.filter(active=status_filter == 'active')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        workflows = workflows.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(workflows, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'workflows': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_workflows': workflows.count(),
        'active_workflows': workflows.filter(active=True).count(),
    }
    
    return render(request, 'core/workflow_list.html', context)


@login_required
def workflow_detail(request, pk):
    """Detail view for an approval workflow."""
    company = request.user.company
    workflow = get_object_or_404(ApprovalWorkflow, pk=pk, company=company)
    
    # Get approval requests for this workflow
    requests = workflow.approval_requests.all().select_related(
        'created_by', 'workflow'
    ).order_by('-created_at')
    
    # Get approval statistics
    stats = {
        'total': requests.count(),
        'pending': requests.filter(status='pending').count(),
        'approved': requests.filter(status='approved').count(),
        'rejected': requests.filter(status='rejected').count(),
        'cancelled': requests.filter(status='cancelled').count(),
    }
    
    context = {
        'workflow': workflow,
        'requests': requests[:10],  # Last 10 requests
        'stats': stats,
    }
    
    return render(request, 'core/workflow_detail.html', context)


@login_required
def workflow_create(request):
    """Create a new approval workflow."""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            document_type = request.POST.get('document_type')
            amount_threshold = request.POST.get('amount_threshold')
            approval_levels = request.POST.get('approval_levels')
            
            # Parse approval levels JSON
            try:
                levels = json.loads(approval_levels)
            except json.JSONDecodeError:
                messages.error(request, 'Format des niveaux d\'approbation invalide')
                return redirect('core:workflow_create')
            
            # Create workflow
            workflow = ApprovalWorkflow.objects.create(
                name=name,
                description=description,
                document_type=document_type,
                amount_threshold=amount_threshold or 0,
                approval_levels=levels,
                company=request.user.company,
                created_by=request.user
            )
            
            messages.success(request, f'Workflow "{workflow.name}" créé avec succès')
            return redirect('core:workflow_detail', pk=workflow.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {str(e)}')
    
    # Get available document types
    document_types = [
        ('invoice', 'Facture'),
        ('quote', 'Devis'),
        ('purchase_order', 'Bon de commande'),
        ('credit_note', 'Avoir'),
        ('payment', 'Paiement'),
        ('expense', 'Dépense'),
        ('other', 'Autre'),
    ]
    
    context = {
        'document_types': document_types,
    }
    
    return render(request, 'core/workflow_form.html', context)


@login_required
def workflow_edit(request, pk):
    """Edit an approval workflow."""
    company = request.user.company
    workflow = get_object_or_404(ApprovalWorkflow, pk=pk, company=company)
    
    if request.method == 'POST':
        try:
            workflow.name = request.POST.get('name')
            workflow.description = request.POST.get('description')
            workflow.document_type = request.POST.get('document_type')
            workflow.amount_threshold = request.POST.get('amount_threshold') or 0
            workflow.active = request.POST.get('active') == 'on'
            
            # Parse approval levels JSON
            approval_levels = request.POST.get('approval_levels')
            if approval_levels:
                try:
                    levels = json.loads(approval_levels)
                    workflow.approval_levels = levels
                except json.JSONDecodeError:
                    messages.error(request, 'Format des niveaux d\'approbation invalide')
                    return redirect('core:workflow_edit', pk=pk)
            
            workflow.save()
            messages.success(request, f'Workflow "{workflow.name}" mis à jour avec succès')
            return redirect('core:workflow_detail', pk=workflow.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour: {str(e)}')
    
    # Get available document types
    document_types = [
        ('invoice', 'Facture'),
        ('quote', 'Devis'),
        ('purchase_order', 'Bon de commande'),
        ('credit_note', 'Avoir'),
        ('payment', 'Paiement'),
        ('expense', 'Dépense'),
        ('other', 'Autre'),
    ]
    
    context = {
        'workflow': workflow,
        'document_types': document_types,
    }
    
    return render(request, 'core/workflow_form.html', context)


# Approval Request Views
@login_required
def approval_request_list(request):
    """List all approval requests."""
    company = request.user.company
    
    # Get requests based on user role
    if request.user.role == 'admin':
        requests = ApprovalRequest.objects.filter(company=company)
    else:
        # Show requests where user is involved or can approve
        requests = ApprovalRequest.objects.filter(
            Q(company=company) &
            (Q(created_by=request.user) | Q(current_level__lte=request.user.approval_level))
        )
    
    requests = requests.select_related('workflow', 'created_by').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    # Filter by workflow
    workflow_filter = request.GET.get('workflow', '')
    if workflow_filter:
        requests = requests.filter(workflow_id=workflow_filter)
    
    # Filter by document type
    doc_type_filter = request.GET.get('document_type', '')
    if doc_type_filter:
        requests = requests.filter(document_type=doc_type_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        requests = requests.filter(
            Q(workflow__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # Get workflows for filter dropdown
    workflows = ApprovalWorkflow.objects.filter(company=company, active=True)
    
    # Pagination
    paginator = Paginator(requests, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requests': page_obj,
        'workflows': workflows,
        'search_query': search_query,
        'status_filter': status_filter,
        'workflow_filter': workflow_filter,
        'doc_type_filter': doc_type_filter,
        'total_requests': requests.count(),
        'pending_count': requests.filter(status='pending').count(),
        'my_approvals_count': requests.filter(
            current_level__lte=request.user.approval_level,
            status='pending'
        ).count(),
    }
    
    return render(request, 'core/approval_request_list.html', context)


@login_required
def approval_request_detail(request, pk):
    """Detail view for an approval request."""
    company = request.user.company
    approval_request = get_object_or_404(ApprovalRequest, pk=pk, company=company)
    
    # Check if user can view this request
    if (request.user != approval_request.created_by and 
        request.user.approval_level < approval_request.current_level):
        messages.error(request, 'Vous n\'avez pas les permissions pour voir cette demande')
        return redirect('core:approval_request_list')
    
    # Get approval logs
    logs = approval_request.approval_logs.all().select_related('user').order_by('-created_at')
    
    # Get document details if available
    document = None
    if approval_request.document_type and approval_request.document_id:
        try:
            content_type = ContentType.objects.get(model=approval_request.document_type)
            document = content_type.get_object_for_this_type(
                pk=approval_request.document_id
            )
        except:
            pass
    
    context = {
        'approval_request': approval_request,
        'logs': logs,
        'document': document,
        'can_approve': request.user.approval_level >= approval_request.current_level,
        'can_reject': request.user.approval_level >= approval_request.current_level,
    }
    
    return render(request, 'core/approval_request_detail.html', context)


@login_required
def approval_action(request, pk):
    """Handle approval/rejection actions."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    company = request.user.company
    approval_request = get_object_or_404(ApprovalRequest, pk=pk, company=company)
    
    # Check if user can approve/reject
    if request.user.approval_level < approval_request.current_level:
        return JsonResponse({'error': 'Niveau d\'approbation insuffisant'}, status=403)
    
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')
    
    if action not in ['approve', 'reject']:
        return JsonResponse({'error': 'Action invalide'}, status=400)
    
    try:
        if action == 'approve':
            # Move to next level or complete
            if approval_request.current_level < approval_request.total_levels:
                approval_request.current_level += 1
                approval_request.status = 'pending'
            else:
                approval_request.status = 'approved'
                approval_request.completed_at = timezone.now()
        else:  # reject
            approval_request.status = 'rejected'
            approval_request.completed_at = timezone.now()
        
        approval_request.save()
        
        # Create approval log
        ApprovalLog.objects.create(
            approval_request=approval_request,
            user=request.user,
            action=action,
            notes=notes
        )
        
        # Create notification for request creator
        Notification.create_notification(
            user=approval_request.created_by,
            title=f'Demande d\'approbation {action}',
            message=f'Votre demande "{approval_request.workflow.name}" a été {action}',
            notification_type='approval',
            priority='medium',
            action_url=reverse_lazy('core:approval_request_detail', kwargs={'pk': pk}),
            company=company,
            created_by=request.user
        )
        
        messages.success(request, f'Demande {action} avec succès')
        return JsonResponse({'success': True, 'status': approval_request.status})
        
    except Exception as e:
        return JsonResponse({'error': f'Erreur lors de l\'action: {str(e)}'}, status=500)


@login_required
def create_approval_request(request):
    """Create a new approval request."""
    if request.method == 'POST':
        try:
            workflow_id = request.POST.get('workflow')
            document_type = request.POST.get('document_type')
            document_id = request.POST.get('document_id')
            amount = request.POST.get('amount', 0)
            notes = request.POST.get('notes', '')
            
            workflow = ApprovalWorkflow.objects.get(
                pk=workflow_id, 
                company=request.user.company,
                active=True
            )
            
            # Check if amount threshold is met
            if workflow.amount_threshold > 0 and float(amount) < workflow.amount_threshold:
                messages.warning(request, 'Le montant ne nécessite pas d\'approbation')
                return redirect('core:approval_request_list')
            
            # Create approval request
            approval_request = ApprovalRequest.objects.create(
                workflow=workflow,
                document_type=document_type,
                document_id=document_id,
                amount=amount,
                notes=notes,
                current_level=1,
                total_levels=len(workflow.approval_levels),
                company=request.user.company,
                created_by=request.user
            )
            
            messages.success(request, 'Demande d\'approbation créée avec succès')
            return redirect('core:approval_request_detail', pk=approval_request.pk)
            
        except ApprovalWorkflow.DoesNotExist:
            messages.error(request, 'Workflow non trouvé')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {str(e)}')
    
    # Get available workflows
    workflows = ApprovalWorkflow.objects.filter(
        company=request.user.company,
        active=True
    )
    
    # Get available documents for approval
    documents = {
        'invoice': Invoice.objects.filter(company=request.user.company, is_posted=False)[:10],
        'quote': Quote.objects.filter(company=request.user.company, status='draft')[:10],
        'purchase_order': PurchaseOrder.objects.filter(company=request.user.company, status='draft')[:10],
    }
    
    context = {
        'workflows': workflows,
        'documents': documents,
    }
    
    return render(request, 'core/approval_request_form.html', context)


# Dashboard Widget Views
@login_required
def dashboard_widgets(request):
    """Manage dashboard widgets."""
    company = request.user.company
    
    if request.method == 'POST':
        # Handle widget updates
        widget_data = request.POST.get('widget_data')
        if widget_data:
            try:
                data = json.loads(widget_data)
                for widget_id, settings in data.items():
                    widget = DashboardWidget.objects.get(
                        pk=widget_id, 
                        user=request.user,
                        company=company
                    )
                    widget.settings = settings
                    widget.save()
                
                messages.success(request, 'Widgets mis à jour avec succès')
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
    
    # Get user's widgets
    widgets = DashboardWidget.objects.filter(
        user=request.user,
        company=company
    ).order_by('position')
    
    context = {
        'widgets': widgets,
    }
    
    return render(request, 'core/dashboard_widgets.html', context)


# Notification Views
@login_required
def notification_list(request):
    """List user notifications."""
    company = request.user.company
    
    notifications = Notification.objects.filter(
        user=request.user,
        company=company
    ).order_by('-created_at')
    
    # Filter by read status
    read_filter = request.GET.get('read', '')
    if read_filter == 'unread':
        notifications = notifications.filter(read=False)
    elif read_filter == 'read':
        notifications = notifications.filter(read=True)
    
    # Filter by type
    type_filter = request.GET.get('type', '')
    if type_filter:
        notifications = notifications.filter(notification_type=type_filter)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'read_filter': read_filter,
        'type_filter': type_filter,
        'unread_count': notifications.filter(read=False).count(),
    }
    
    return render(request, 'core/notification_list.html', context)


@login_required
def mark_notification_read(request, pk):
    """Mark a notification as read."""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(
                pk=pk, 
                user=request.user,
                company=request.user.company
            )
            notification.mark_as_read()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'error': 'Notification non trouvée'}, status=404)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def dismiss_notification(request, pk):
    """Dismiss a notification."""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(
                pk=pk, 
                user=request.user,
                company=request.user.company
            )
            notification.dismiss()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'error': 'Notification non trouvée'}, status=404)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

# Error handlers
def handler404(request, exception):
    """Custom 404 error handler."""
    return render(request, '404.html', status=404)

def handler500(request):
    """Custom 500 error handler."""
    return render(request, '500.html', status=500)
