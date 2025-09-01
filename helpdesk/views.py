from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Ticket, SLA, TicketComment
import uuid


@login_required
def ticket_list(request):
    qs = Ticket.objects.filter(company=request.user.company).select_related('requester', 'assignee', 'sla')
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    priority = request.GET.get('priority')
    if priority:
        qs = qs.filter(priority=priority)
    return render(request, 'helpdesk/ticket_list.html', {'tickets': qs})


@login_required
def ticket_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'normal')
        sla_id = request.POST.get('sla')
        if not title:
            messages.error(request, 'Le titre est requis.')
        else:
            number = f"TIC-{timezone.now().year}-{uuid.uuid4().hex[:6].upper()}"
            sla = SLA.objects.filter(pk=sla_id, company=request.user.company, active=True).first() if sla_id else None
            due_at = None
            if sla:
                due_at = timezone.now() + timezone.timedelta(hours=sla.resolution_time_hours)
            ticket = Ticket.objects.create(
                number=number,
                title=title,
                description=description,
                priority=priority,
                sla=sla,
                requester=request.user,
                company=request.user.company,
                due_at=due_at,
            )
            messages.success(request, 'Ticket créé avec succès.')
            return redirect('helpdesk:ticket_detail', pk=ticket.pk)
    slas = SLA.objects.filter(company=request.user.company, active=True)
    return render(request, 'helpdesk/ticket_form.html', {'slas': slas})


@login_required
def ticket_detail(request, pk: int):
    ticket = get_object_or_404(Ticket, pk=pk, company=request.user.company)
    return render(request, 'helpdesk/ticket_detail.html', {'ticket': ticket})


@login_required
def ticket_comment(request, pk: int):
    ticket = get_object_or_404(Ticket, pk=pk, company=request.user.company)
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            TicketComment.objects.create(ticket=ticket, author=request.user, message=message)
            messages.success(request, 'Commentaire ajouté.')
        return redirect('helpdesk:ticket_detail', pk=pk)
    return redirect('helpdesk:ticket_detail', pk=pk)


@login_required
def my_ticket_list(request):
    qs = Ticket.objects.filter(company=request.user.company, requester=request.user).select_related('assignee', 'sla')
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    priority = request.GET.get('priority')
    if priority:
        qs = qs.filter(priority=priority)
    return render(request, 'helpdesk/my_ticket_list.html', {'tickets': qs})


@login_required
def sla_list(request):
    if not request.user.is_staff:
        messages.error(request, "Accès refusé.")
        return redirect('helpdesk:ticket_list')
    slas = SLA.objects.filter(company=request.user.company).order_by('name')
    return render(request, 'helpdesk/sla_list.html', {'slas': slas})


@login_required
def sla_create(request):
    if not request.user.is_staff:
        messages.error(request, "Accès refusé.")
        return redirect('helpdesk:ticket_list')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        response = request.POST.get('response_time_hours')
        resolution = request.POST.get('resolution_time_hours')
        active = request.POST.get('active') == 'on'
        if not name:
            messages.error(request, 'Le nom est requis.')
        else:
            try:
                response_h = int(response or 0)
                resolution_h = int(resolution or 0)
            except ValueError:
                messages.error(request, 'Les délais doivent être des nombres.')
                return render(request, 'helpdesk/sla_form.html')
            SLA.objects.create(
                name=name,
                response_time_hours=response_h,
                resolution_time_hours=resolution_h,
                active=active,
                company=request.user.company,
            )
            messages.success(request, 'SLA créé avec succès.')
            return redirect('helpdesk:sla_list')
    return render(request, 'helpdesk/sla_form.html')


