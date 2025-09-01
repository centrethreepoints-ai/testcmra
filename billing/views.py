"""
Views for billing application.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.urls import reverse, reverse_lazy
from django.forms import formset_factory
from django.contrib.contenttypes.models import ContentType
from datetime import datetime
import uuid
from decimal import Decimal
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from weasyprint import HTML
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from crm.models import Party
from .utils import generate_qr_data_uri
from core.models import ApprovalWorkflow, ApprovalRequest, Notification
from core.decorators import role_required


from .models import Quote, PurchaseOrder, Invoice, CreditNote, Payment, DocumentLine, EmailTemplate, EmailLog
from .forms import QuoteForm, PurchaseOrderForm, InvoiceForm, CreditNoteForm, DocumentLineForm, PaymentQuickForm


@login_required
def quote_list(request):
    quotes = Quote.objects.filter(company=request.user.company).order_by('-issue_date', '-id')
    # Text filters
    client_query = request.GET.get('client', '')
    text_search = request.GET.get('search', '')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status = request.GET.get('status')
    if client_query:
        quotes = quotes.filter(party__name__icontains=client_query)
    if text_search:
        quotes = quotes.filter(
            party__name__icontains=text_search
        ) | quotes.filter(number__icontains=text_search)
    if date_from:
        quotes = quotes.filter(issue_date__gte=date_from)
    if date_to:
        quotes = quotes.filter(issue_date__lte=date_to)
    if status:
        quotes = quotes.filter(status=status)
    # Ensure final ordering after filters
    quotes = quotes.order_by('-issue_date', '-id')
    # Aggregates on the filtered queryset
    total_values = quotes.values_list('total_ttc', flat=True)
    total_sum = sum(((v or Decimal('0.00')) for v in total_values), Decimal('0.00'))
    total_quotes = quotes.count()
    validated_count = quotes.filter(status='validated').count()
    pending_count = quotes.filter(status__in=['draft', 'sent', 'approved']).count()
    return render(request, 'billing/quote_list.html', {
        'quotes': quotes,
        'party_selected': '',
        'date_from': date_from or '',
        'date_to': date_to or '',
        'status_selected': status or '',
        'client_query': client_query or '',
        'search_query': text_search or '',
        'total_sum': total_sum,
        'total_quotes': total_quotes,
        'validated_count': validated_count,
        'pending_count': pending_count,
    })


# --- Helpers (email + pdf) ---
def _get_or_create_default_template(company, user, template_type: str) -> EmailTemplate:
    name_map = {
        'quote': 'Modèle Devis Par Défaut',
        'purchase_order': 'Modèle Bon de Commande Par Défaut',
        'invoice': 'Modèle Facture Par Défaut',
    }
    subject_map = {
        'quote': 'Devis {{ document.number }}',
        'purchase_order': 'Bon de commande {{ document.number }}',
        'invoice': 'Facture {{ document.number }}',
    }
    body_default = (
        'Bonjour,\n\nVeuillez trouver ci-joint {{ document_label }} {{ document.number }}.\n'
        'Lien: {{ document_url }}\n\nCordialement.'
    )
    template, _ = EmailTemplate.objects.get_or_create(
        company=company,
        name=name_map.get(template_type, f"Modèle {template_type}"),
        defaults={
            'subject': subject_map.get(template_type, '{{ document.number }}'),
            'body': body_default,
            'template_type': template_type,
            'available_variables': 'document, document_url, document_label, company',
            'created_by': user,
            'active': True,
        }
    )
    return template


def _render_quote_pdf_bytes(request, quote) -> bytes:
    lines = quote.lines.all()
    company = request.user.company
    logo_src = None
    try:
        if getattr(company, 'logo', None) and company.logo:
            logo_src = company.logo.path
    except Exception:
        logo_src = None
    try:
        detail_url = request.build_absolute_uri(reverse('billing:quote_detail', args=[quote.pk]))
        qr_data_uri = generate_qr_data_uri(detail_url)
    except Exception:
        qr_data_uri = None
    html = render_to_string('billing/pdf/quote_pdf.html', {
        'quote': quote,
        'lines': lines,
        'company': company,
        'logo_src': logo_src,
        'qr_data_uri': qr_data_uri,
    }, request=request)
    return HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()


def _render_po_pdf_bytes(request, po) -> bytes:
    lines = po.lines.all()
    company = request.user.company
    logo_src = None
    try:
        if getattr(company, 'logo', None) and company.logo:
            logo_src = company.logo.path
    except Exception:
        logo_src = None
    try:
        detail_url = request.build_absolute_uri(reverse('billing:purchase_order_detail', args=[po.pk]))
        qr_data_uri = generate_qr_data_uri(detail_url)
    except Exception:
        qr_data_uri = None
    html = render_to_string('billing/pdf/purchase_order_pdf.html', {
        'po': po,
        'lines': lines,
        'company': company,
        'logo_src': logo_src,
        'qr_data_uri': qr_data_uri,
    }, request=request)
    return HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()


def _render_invoice_pdf_bytes(request, invoice) -> bytes:
    lines = invoice.lines.all()
    company = request.user.company
    logo_src = None
    try:
        if getattr(company, 'logo', None) and company.logo:
            logo_src = company.logo.path
    except Exception:
        logo_src = None
    try:
        detail_url = request.build_absolute_uri(reverse('billing:invoice_detail', args=[invoice.pk]))
        qr_data_uri = generate_qr_data_uri(detail_url)
    except Exception:
        qr_data_uri = None
    html = render_to_string('billing/pdf/invoice_pdf.html', {
        'invoice': invoice,
        'lines': lines,
        'company': company,
        'logo_src': logo_src,
        'qr_data_uri': qr_data_uri,
    }, request=request)
    return HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()


@login_required
def quote_detail(request, pk):
    quote = get_object_or_404(Quote, pk=pk, company=request.user.company)
    lines = quote.lines.all()
    return render(request, 'billing/quote_detail.html', {'quote': quote, 'lines': lines})


@login_required
@role_required('vente')
def quote_create(request):
    def formset_factory_with_user(user):
        BaseFS = formset_factory(DocumentLineForm, extra=1, can_delete=False)
        class UserBoundFormSet(BaseFS):
            def _construct_form(self, i, **kwargs):
                kwargs['user'] = user
                return super()._construct_form(i, **kwargs)
        return UserBoundFormSet
    LineFormSet = formset_factory_with_user(request.user)
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        formset = LineFormSet(request.POST, prefix='lines')
        if form.is_valid() and formset.is_valid():
            quote = form.save(commit=False)
            quote.company = request.user.company
            quote.sequence_code = 'DEV'
            quote.number = f"DEV-DRAFT-{uuid.uuid4().hex[:8]}"
            quote.save()
            any_line = False
            for lf in formset:
                if lf.cleaned_data:
                    line = lf.save(commit=False)
                    quote.lines.create(
                        product=line.product,
                        description=line.description,
                        quantity=line.quantity,
                        unit_price_ht=line.unit_price_ht,
                        discount_percent=line.discount_percent,
                        tax_rate=line.tax_rate,
                    )
                    any_line = True
            if not any_line:
                messages.error(request, "Veuillez ajouter au moins une ligne valide.")
                return render(request, 'billing/quote_form.html', {'form': form, 'formset': formset})
            quote.calculate_totals()
            year = datetime.now().year
            quote.number = f"DEV-{year}-{quote.id:04d}"
            quote.save()
            # Créer une demande d'approbation si activé et nécessaire
            if request.user.company.get_preference('feature_approvals_enabled', True):
                try:
                    workflows = ApprovalWorkflow.objects.filter(
                        company=quote.company, document_type='quote', active=True
                    )
                    for wf in workflows:
                        needs_amount = bool(wf.amount_threshold and quote.total_ttc and quote.total_ttc >= wf.amount_threshold)
                        needs_discount = bool(quote.discount_percent and quote.discount_percent > 0)
                        if needs_amount or needs_discount:
                            ApprovalRequest.objects.create(
                                workflow=wf,
                                document_type='quote',
                                document_id=quote.id,
                                amount=quote.total_ttc,
                                current_level=1,
                                total_levels=len(wf.approval_levels or []),
                                company=quote.company,
                                created_by=request.user,
                            )
                            messages.info(request, "Demande d'approbation créée pour ce devis.")
                            break
                except Exception:
                    pass
            messages.success(request, f"Devis {quote.number} créé avec succès.")
            return redirect('billing:quote_detail', pk=quote.pk)
        else:
            messages.error(request, "Formulaire invalide. Vérifiez les champs en rouge.")
    else:
        form = QuoteForm()
        formset = LineFormSet(prefix='lines')
    return render(request, 'billing/quote_form.html', {'form': form, 'formset': formset})


@login_required
@role_required('vente')
def quote_add_line(request):
    try:
        total = int(request.GET.get('lines-TOTAL_FORMS', '0'))
    except (TypeError, ValueError):
        total = 0
    index = total
    form = DocumentLineForm(prefix=f'lines-{index}', user=request.user)
    context = {
        'form': form,
        'index': index,
        'new_total': index + 1,
    }
    return render(request, 'billing/fragments/line_row.html', context)


@login_required
@role_required('vente')
def quote_edit(request, pk):
    quote = get_object_or_404(Quote, pk=pk, company=request.user.company)
    if request.method == 'POST':
        return redirect('billing:quote_detail', pk=quote.pk)
    return render(request, 'billing/quote_form.html', {'quote': quote})


@login_required
@role_required('vente')
def quote_delete(request, pk):
    quote = get_object_or_404(Quote, pk=pk, company=request.user.company)
    if request.method == 'POST':
        # quote.delete()  # à activer plus tard
        return redirect('billing:quote_list')
    return render(request, 'billing/quote_confirm_delete.html', {'object': quote})


@login_required
@role_required('vente')
def quote_to_po(request, pk):
    quote = get_object_or_404(Quote, pk=pk, company=request.user.company)
    # Bloquer la conversion si une approbation est en attente
    try:
        if ApprovalRequest.objects.filter(
            company=quote.company,
            document_type='quote',
            document_id=quote.id,
            status='pending',
        ).exists():
            messages.error(request, "Conversion bloquée: approbation en attente pour ce devis.")
            return redirect('billing:quote_detail', pk=quote.pk)
    except Exception:
        pass
    if request.method == 'POST':
        tmp_number = f"BC-DRAFT-{uuid.uuid4().hex[:8]}"
        po = PurchaseOrder.objects.create(
            company=quote.company,
            party=quote.party,
            currency=quote.currency,
            exchange_rate=quote.exchange_rate,
            discount_percent=quote.discount_percent,
            withholding_tax_percent=quote.withholding_tax_percent,
            notes=quote.notes,
            terms=quote.terms,
            order_type='sale',
            sequence_code='BC',
            number=tmp_number,
        )
        for line in quote.lines.all():
            po.lines.create(
                product=line.product,
                description=line.description,
                quantity=line.quantity,
                unit_price_ht=line.unit_price_ht,
                discount_percent=line.discount_percent,
                tax_rate=line.tax_rate,
            )
        po.calculate_totals()
        year = datetime.now().year
        po.number = f"BC-{year}-{po.id:04d}"
        po.save()
        from django.utils import timezone
        quote.is_converted = True
        quote.converted_po = po
        quote.converted_at = timezone.now()
        quote.status = 'sent'
        quote.save(update_fields=['is_converted', 'converted_po', 'converted_at', 'status'])
        return redirect('billing:purchase_order_detail', pk=po.pk)
    return render(request, 'billing/actions/quote_to_po_confirm.html', {'quote': quote})


@login_required
@role_required('vente')
def quote_mark_sent(request, pk):
    quote = get_object_or_404(Quote, pk=pk, company=request.user.company)
    quote.status = 'sent'
    quote.save(update_fields=['status'])
    # Send email with PDF if email available
    try:
        if request.user.company.get_preference('feature_emails_enabled', True):
            recipient = (quote.party.email or '').strip()
            if recipient:
                template = _get_or_create_default_template(request.user.company, request.user, 'quote')
                context = {
                    'document': quote,
                    'document_label': 'devis',
                    'document_url': request.build_absolute_uri(reverse('billing:quote_detail', args=[quote.pk])),
                    'company': request.user.company,
                }
                subject = template.get_rendered_subject(context)
                body = template.get_rendered_body(context)
                log = EmailLog.objects.create(
                    template=template,
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    context_data=context,
                    company=request.user.company,
                    created_by=request.user,
                    status='pending',
                )
                pdf_bytes = _render_quote_pdf_bytes(request, quote)
                email = EmailMessage(subject, body, to=[recipient])
                email.attach(f"Devis-{quote.number}.pdf", pdf_bytes, 'application/pdf')
                email.send(fail_silently=True)
                log.mark_as_sent()
                messages.success(request, "Devis envoyé par email.")
    except Exception:
        # Non bloquant
        pass
    return redirect('billing:quote_list')


@login_required
@role_required('vente')
def purchase_order_mark_sent(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    po.status = 'sent'
    po.save(update_fields=['status'])
    try:
        if request.user.company.get_preference('feature_emails_enabled', True):
            recipient = (po.party.email or '').strip()
            if recipient:
                template = _get_or_create_default_template(request.user.company, request.user, 'purchase_order')
                context = {
                    'document': po,
                    'document_label': 'bon de commande',
                    'document_url': request.build_absolute_uri(reverse('billing:purchase_order_detail', args=[po.pk])),
                    'company': request.user.company,
                }
                subject = template.get_rendered_subject(context)
                body = template.get_rendered_body(context)
                log = EmailLog.objects.create(
                    template=template,
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    context_data=context,
                    company=request.user.company,
                    created_by=request.user,
                    status='pending',
                )
                pdf_bytes = _render_po_pdf_bytes(request, po)
                email = EmailMessage(subject, body, to=[recipient])
                email.attach(f"BC-{po.number}.pdf", pdf_bytes, 'application/pdf')
                email.send(fail_silently=True)
                log.mark_as_sent()
                messages.success(request, "Bon de commande envoyé par email.")
    except Exception:
        pass
    return redirect('billing:purchase_order_list')


@login_required
@role_required('comptable')
def invoice_mark_validated(request, pk):
    inv = get_object_or_404(Invoice, pk=pk, company=request.user.company)
    if inv.status != 'sent':
        messages.error(request, "La facture doit être envoyée avant d'être confirmée.")
        return redirect('billing:invoice_detail', pk=inv.pk)
    # Block if approval pending
    try:
        if ApprovalRequest.objects.filter(
            company=inv.company,
            document_type='invoice',
            document_id=inv.id,
            status='pending',
        ).exists():
            messages.error(request, "Validation bloquée: approbation en attente pour cette facture.")
            return redirect('billing:invoice_detail', pk=inv.pk)
    except Exception:
        pass
    inv.status = 'validated'
    inv.save(update_fields=['status'])
    # Inventory movements on validation
    try:
        from catalog.models import StockMovement
        # Only sales invoices move stock OUT on validation. Purchases are received at PO confirmation.
        if inv.invoice_type == 'sale':
            if not StockMovement.objects.filter(company=inv.company, reference=inv.number, reference_type='invoice').exists():
                for line in inv.lines.select_related('product').all():
                    product = getattr(line, 'product', None)
                    if not product or not getattr(product, 'has_stock', False):
                        continue
                    if getattr(product, 'product_type', '') == 'service':
                        continue
                    StockMovement.objects.create(
                        product=product,
                        movement_type='out',
                        quantity=line.quantity,
                        unit_cost=line.unit_price_ht,
                        reference=inv.number,
                        reference_type='invoice',
                        reference_id=inv.id,
                        stock_before=product.current_stock,
                        notes="Auto out on sales invoice validation",
                        company=inv.company,
                        created_by=request.user,
                    )
        elif inv.invoice_type == 'purchase':
            # Optional feature: increase stock on purchase invoice validation
            enable_in_on_invoice = True
            try:
                enable_in_on_invoice = inv.company.get_preference('feature_stock_in_on_purchase_invoice', True)
            except Exception:
                enable_in_on_invoice = True
            if enable_in_on_invoice and not StockMovement.objects.filter(company=inv.company, reference=inv.number, reference_type='invoice').exists():
                for line in inv.lines.select_related('product').all():
                    product = getattr(line, 'product', None)
                    if not product or not getattr(product, 'has_stock', False):
                        continue
                    if getattr(product, 'product_type', '') == 'service':
                        continue
                    StockMovement.objects.create(
                        product=product,
                        movement_type='in',
                        quantity=line.quantity,
                        unit_cost=line.unit_price_ht,
                        reference=inv.number,
                        reference_type='invoice',
                        reference_id=inv.id,
                        stock_before=product.current_stock,
                        notes="Auto in on purchase invoice validation",
                        company=inv.company,
                        created_by=request.user,
                    )
    except Exception:
        # Best-effort; don't block validation if stock update fails
        pass
    # Comptabiliser automatiquement la facture selon type à la confirmation
    try:
        from accounting.services.posting import post_customer_invoice, post_supplier_invoice
        if inv.invoice_type == 'sale':
            post_customer_invoice(inv.company, inv)
        elif inv.invoice_type == 'purchase':
            post_supplier_invoice(inv.company, inv)
    except Exception:
        pass
    return redirect('billing:invoice_list')


@login_required
@role_required('vente')
def invoice_mark_sent(request, pk):
    inv = get_object_or_404(Invoice, pk=pk, company=request.user.company)
    if request.method == 'POST':
        if inv.status == 'draft':
            inv.status = 'sent'
            inv.save(update_fields=['status'])
            try:
                if request.user.company.get_preference('feature_emails_enabled', True):
                    recipient = (inv.party.email or '').strip()
                    if recipient:
                        template = _get_or_create_default_template(request.user.company, request.user, 'invoice')
                        context = {
                            'document': inv,
                            'document_label': 'facture',
                            'document_url': request.build_absolute_uri(reverse('billing:invoice_detail', args=[inv.pk])),
                            'company': request.user.company,
                        }
                        subject = template.get_rendered_subject(context)
                        body = template.get_rendered_body(context)
                        log = EmailLog.objects.create(
                            template=template,
                            recipient=recipient,
                            subject=subject,
                            body=body,
                            context_data=context,
                            company=request.user.company,
                            created_by=request.user,
                            status='pending',
                        )
                        pdf_bytes = _render_invoice_pdf_bytes(request, inv)
                        email = EmailMessage(subject, body, to=[recipient])
                        email.attach(f"FACTURE-{inv.number}.pdf", pdf_bytes, 'application/pdf')
                        email.send(fail_silently=True)
                        log.mark_as_sent()
                        messages.success(request, "Facture envoyée par email et marquée comme envoyée.")
                    else:
                        messages.success(request, "Facture marquée comme envoyée.")
            except Exception:
                messages.success(request, "Facture marquée comme envoyée.")
        return redirect('billing:invoice_detail', pk=inv.pk)
    return redirect('billing:invoice_detail', pk=inv.pk)


@login_required
@role_required('vente')
def purchase_order_detail(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    # Fallback: si aucune ligne, tenter de reconstruire depuis le devis d'origine
    if not po.lines.exists():
        origin_quote = Quote.objects.filter(converted_po=po).first()
        if origin_quote:
            for l in origin_quote.lines.all():
                po.lines.create(
                    product=l.product,
                    description=l.description,
                    quantity=l.quantity,
                    unit_price_ht=l.unit_price_ht,
                    discount_percent=l.discount_percent,
                    tax_rate=l.tax_rate,
                )
            po.calculate_totals()
            po.save()
    lines = po.lines.all()
    po_reception_enabled = request.user.company.get_preference('feature_po_reception_enabled', True)
    return render(request, 'billing/purchase_order_detail.html', {
        'po': po,
        'lines': lines,
        'po_reception_enabled': po_reception_enabled,
    })


@login_required
@role_required('vente')
def po_to_invoice(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    if request.method == 'POST':
        # Enforce confirmation step for purchase and sales orders
        if po.status != 'validated':
            messages.error(request, "Le bon de commande doit être confirmé avant de créer la facture.")
            return redirect('billing:purchase_order_detail', pk=po.pk)
        tmp_number = f"FAC-DRAFT-{uuid.uuid4().hex[:8]}"
        inv = Invoice.objects.create(
            company=po.company,
            party=po.party,
            currency=po.currency,
            exchange_rate=po.exchange_rate,
            discount_percent=po.discount_percent,
            withholding_tax_percent=po.withholding_tax_percent,
            notes=po.notes,
            terms=po.terms,
            invoice_type='sale',
            purchase_order=po,
            sequence_code='FAC',
            number=tmp_number,
        )
        for line in po.lines.all():
            inv.lines.create(
                product=line.product,
                description=line.description,
                quantity=line.quantity,
                unit_price_ht=line.unit_price_ht,
                discount_percent=line.discount_percent,
                tax_rate=line.tax_rate,
            )
        inv.calculate_totals()
        year = datetime.now().year
        inv.number = f"FAC-{year}-{inv.id:04d}"
        inv.save()
        from django.utils import timezone
        po.converted_invoice = inv
        po.converted_at = timezone.now()
        po.save(update_fields=['converted_invoice', 'converted_at'])
        # Inventory movements on conversion for purchase orders: for 'purchase' add stock; for 'sale' subtract stock
        try:
            from catalog.models import StockMovement
            if not StockMovement.objects.filter(company=po.company, reference=po.number, reference_type='po').exists():
                for line in po.lines.select_related('product').all():
                    product = getattr(line, 'product', None)
                    if not product or not getattr(product, 'has_stock', False):
                        continue
                    if getattr(product, 'product_type', '') == 'service':
                        continue
                    movement_type = 'in' if po.order_type == 'purchase' else 'out'
                    StockMovement.objects.create(
                        product=product,
                        movement_type=movement_type,
                        quantity=line.quantity,
                        unit_cost=line.unit_price_ht,
                        reference=po.number,
                        reference_type='po',
                        reference_id=po.id,
                        stock_before=product.current_stock,
                        notes=f"Auto {movement_type} on PO conversion",
                        company=po.company,
                        created_by=request.user,
                    )
        except Exception:
            pass
        # Comptabilisation simplifiée facture client
        try:
            from accounting.services.posting import post_customer_invoice
            post_customer_invoice(inv.company, inv)
        except Exception:
            pass
        return redirect('billing:invoice_detail', pk=inv.pk)
    return render(request, 'billing/actions/po_to_invoice_confirm.html', {'po': po})


@login_required
@role_required('vente')
def purchase_order_confirm(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    if request.method == 'POST':
        if po.status != 'sent':
            messages.error(request, "Le bon de commande doit être envoyé avant d'être confirmé.")
            return redirect('billing:purchase_order_detail', pk=po.pk)
        # Block if approval pending
        try:
            if ApprovalRequest.objects.filter(
                company=po.company,
                document_type='purchase_order',
                document_id=po.id,
                status='pending',
            ).exists():
                messages.error(request, "Confirmation bloquée: approbation en attente pour ce BC.")
                return redirect('billing:purchase_order_detail', pk=po.pk)
        except Exception:
            pass
        po.status = 'validated'
        po.save(update_fields=['status'])
        # For purchase orders, registering incoming stock on confirmation unless reception feature enabled
        if po.order_type == 'purchase' and not request.user.company.get_preference('feature_po_reception_enabled', True):
            try:
                from catalog.models import StockMovement
                if not StockMovement.objects.filter(company=po.company, reference=po.number, reference_type='po').exists():
                    for line in po.lines.select_related('product').all():
                        product = getattr(line, 'product', None)
                        if not product or not getattr(product, 'has_stock', False):
                            continue
                        if getattr(product, 'product_type', '') == 'service':
                            continue
                        StockMovement.objects.create(
                            product=product,
                            movement_type='in',
                            quantity=line.quantity,
                            unit_cost=line.unit_price_ht,
                            reference=po.number,
                            reference_type='po',
                            reference_id=po.id,
                            stock_before=product.current_stock,
                            notes="Auto in on PO confirmation",
                            company=po.company,
                            created_by=request.user,
                        )
            except Exception:
                pass
        messages.success(request, "Bon de commande confirmé.")
        return redirect('billing:purchase_order_detail', pk=po.pk)
    return render(request, 'billing/actions/purchase_order_confirm.html', {'po': po})


@login_required
@role_required('vente')
def purchase_order_receive(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    if request.method == 'POST':
        # Require feature enabled
        if not request.user.company.get_preference('feature_po_reception_enabled', True):
            messages.error(request, "La réception est désactivée par les paramètres.")
            return redirect('billing:purchase_order_detail', pk=po.pk)
        # Only for purchase orders
        if po.order_type != 'purchase':
            messages.error(request, "La réception ne s'applique qu'aux bons de commande d'achat.")
            return redirect('billing:purchase_order_detail', pk=po.pk)
        # Create IN stock movements if not already
        try:
            from catalog.models import StockMovement
            if not StockMovement.objects.filter(company=po.company, reference=po.number, reference_type='po').exists():
                for line in po.lines.select_related('product').all():
                    product = getattr(line, 'product', None)
                    if not product or not getattr(product, 'has_stock', False):
                        continue
                    if getattr(product, 'product_type', '') == 'service':
                        continue
                    StockMovement.objects.create(
                        product=product,
                        movement_type='in',
                        quantity=line.quantity,
                        unit_cost=line.unit_price_ht,
                        reference=po.number,
                        reference_type='po',
                        reference_id=po.id,
                        stock_before=product.current_stock,
                        notes="Réception BC",
                        company=po.company,
                        created_by=request.user,
                    )
                messages.success(request, "Réception enregistrée (entrées de stock créées).")
            else:
                messages.info(request, "Réception déjà enregistrée pour ce BC.")
        except Exception:
            messages.error(request, "Erreur lors de la réception.")
        return redirect('billing:purchase_order_detail', pk=po.pk)
    return redirect('billing:purchase_order_detail', pk=po.pk)


@login_required
@role_required('comptable')
def invoice_quick_pay(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)
    if request.method == 'POST':
        form = PaymentQuickForm(request.POST)
        if form.is_valid():
            payment = Payment.objects.create(
                company=invoice.company,
                party=invoice.party,
                amount=form.cleaned_data['amount'],
                method=form.cleaned_data['method'],
                reference=form.cleaned_data.get('reference','')
            )
            # Allocation partielle/complète à la facture
            from .models import PaymentAllocation
            from decimal import Decimal
            ct = ContentType.objects.get_for_model(invoice)
            remaining = invoice.get_remaining_amount()
            allocate_amount = form.cleaned_data['amount']
            if allocate_amount > remaining:
                allocate_amount = remaining
            if allocate_amount > Decimal('0.00'):
                PaymentAllocation.objects.create(
                    payment=payment,
                    content_type=ct,
                    document_id=invoice.id,
                    allocated_amount=allocate_amount,
                )
            # Mettre à jour le statut de la facture
            paid = invoice.get_paid_amount()
            if paid >= invoice.total_ttc:
                invoice.status = 'paid'
            elif paid > 0:
                invoice.status = 'partial'
            invoice.save(update_fields=['status'])
            messages.success(request, "Paiement enregistré et alloué à la facture.")
            return redirect('billing:invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, "Formulaire invalide. Vérifiez les champs en rouge.")
    else:
        form = PaymentQuickForm(initial={'amount': invoice.get_remaining_amount()})
    return render(request, 'billing/actions/invoice_quick_pay.html', {'invoice': invoice, 'form': form})


@login_required
def invoice_list(request):
    invoices = Invoice.objects.filter(company=request.user.company).order_by('-issue_date', '-id')
    party_id = request.GET.get('party')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status = request.GET.get('status')
    inv_type = request.GET.get('type')  # 'sale' or 'purchase'
    if inv_type == 'sale':
        invoices = invoices.filter(invoice_type='sale')
    elif inv_type == 'purchase':
        invoices = invoices.filter(invoice_type='purchase')
    if party_id:
        invoices = invoices.filter(party_id=party_id)
    if date_from:
        invoices = invoices.filter(issue_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(issue_date__lte=date_to)
    if status:
        if status == 'unpaid':
            invoices = invoices.exclude(status__in=['paid', 'cancelled'])
        else:
            valid_statuses = {'draft', 'sent', 'approved', 'validated', 'partial', 'paid', 'cancelled'}
            if status in valid_statuses:
                invoices = invoices.filter(status=status)
    # Ensure final ordering after filters
    invoices = invoices.order_by('-issue_date', '-id')
    total_values = invoices.values_list('total_ttc', flat=True)
    total_sum = sum(((v or Decimal('0.00')) for v in total_values), Decimal('0.00'))
    parties = Party.objects.filter(company=request.user.company).order_by('name')
    counts = {
        'all': Invoice.objects.filter(company=request.user.company).count(),
        'sale': Invoice.objects.filter(company=request.user.company, invoice_type='sale').count(),
        'purchase': Invoice.objects.filter(company=request.user.company, invoice_type='purchase').count(),
    }
    return render(request, 'billing/invoice_list.html', {
        'invoices': invoices,
        'parties': parties,
        'party_selected': party_id or '',
        'date_from': date_from or '',
        'date_to': date_to or '',
        'status_selected': status or '',
        'total_sum': total_sum,
        'filter_type': inv_type or '',
        'counts': counts,
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)
    from .models import PaymentAllocation
    ct = ContentType.objects.get_for_model(invoice)
    allocations = PaymentAllocation.objects.filter(content_type=ct, document_id=invoice.id).select_related('payment').order_by('-payment__date', '-id')
    paid_amount = invoice.get_paid_amount()
    remaining_amount = invoice.get_remaining_amount()
    return render(request, 'billing/invoice_detail.html', {
        'invoice': invoice,
        'allocations': allocations,
        'paid_amount': paid_amount,
        'remaining_amount': remaining_amount,
    })


@login_required
def invoice_create(request):
    def formset_factory_with_user(user):
        BaseFS = formset_factory(DocumentLineForm, extra=1, can_delete=False)
        class UserBoundFormSet(BaseFS):
            def _construct_form(self, i, **kwargs):
                kwargs['user'] = user
                return super()._construct_form(i, **kwargs)
        return UserBoundFormSet
    LineFormSet = formset_factory_with_user(request.user)
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = LineFormSet(request.POST, prefix='lines')
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.company = request.user.company
            invoice.sequence_code = 'FAC'
            invoice.number = f"FAC-DRAFT-{uuid.uuid4().hex[:8]}"
            invoice.save()
            any_line = False
            for lf in formset:
                if lf.cleaned_data:
                    line = lf.save(commit=False)
                    invoice.lines.create(
                        product=line.product,
                        description=line.description,
                        quantity=line.quantity,
                        unit_price_ht=line.unit_price_ht,
                        discount_percent=line.discount_percent,
                        tax_rate=line.tax_rate,
                    )
                    any_line = True
            if not any_line:
                messages.error(request, "Veuillez ajouter au moins une ligne valide.")
                return render(request, 'billing/invoice_form.html', {'form': form, 'formset': formset})
            invoice.calculate_totals()
            year = datetime.now().year
            invoice.number = f"FAC-{year}-{invoice.id:04d}"
            invoice.save()
            # Approval if needed and enabled for invoices
            if request.user.company.get_preference('feature_approvals_enabled', True):
                try:
                    workflows = ApprovalWorkflow.objects.filter(
                        company=invoice.company, document_type='invoice', active=True
                    )
                    for wf in workflows:
                        needs_amount = bool(wf.amount_threshold and invoice.total_ttc and invoice.total_ttc >= wf.amount_threshold)
                        if needs_amount:
                            ApprovalRequest.objects.create(
                                workflow=wf,
                                document_type='invoice',
                                document_id=invoice.id,
                                amount=invoice.total_ttc,
                                current_level=1,
                                total_levels=len(wf.approval_levels or []),
                                company=invoice.company,
                                created_by=request.user,
                            )
                            messages.info(request, "Demande d'approbation créée pour cette facture.")
                            break
                except Exception:
                    pass
            messages.success(request, f"Facture {invoice.number} créée avec succès.")
            return redirect('billing:invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, "Formulaire invalide. Vérifiez les champs en rouge.")
    else:
        form = InvoiceForm()
        formset = LineFormSet(prefix='lines')
    return render(request, 'billing/invoice_form.html', {'form': form, 'formset': formset})


@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)
    if request.method == 'POST':
        return redirect('billing:invoice_detail', pk=invoice.pk)
    return render(request, 'billing/invoice_form.html', {'invoice': invoice})


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)
    if request.method == 'POST':
        # invoice.delete()  # à activer plus tard
        return redirect('billing:invoice_list')
    return render(request, 'billing/invoice_confirm_delete.html', {'object': invoice})


@login_required
def payment_list(request):
    payments = Payment.objects.filter(company=request.user.company).order_by('-date')
    return render(request, 'billing/payment_list.html', {'payments': payments})


@login_required
def payment_create(request):
    if request.method == 'POST':
        return redirect('billing:payment_list')
    return render(request, 'billing/payment_form.html', {})


@login_required
def purchase_order_list(request):
    pos = PurchaseOrder.objects.filter(company=request.user.company).order_by('-issue_date', '-id')
    party_id = request.GET.get('party')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status = request.GET.get('status')
    if party_id:
        pos = pos.filter(party_id=party_id)
    if date_from:
        pos = pos.filter(issue_date__gte=date_from)
    if date_to:
        pos = pos.filter(issue_date__lte=date_to)
    if status:
        pos = pos.filter(status=status)
    # Ensure final ordering after filters
    pos = pos.order_by('-issue_date', '-id')
    total_values = pos.values_list('total_ttc', flat=True)
    total_sum = sum(((v or Decimal('0.00')) for v in total_values), Decimal('0.00'))
    parties = Party.objects.filter(company=request.user.company).order_by('name')
    return render(request, 'billing/purchase_order_list.html', {
        'purchase_orders': pos,
        'parties': parties,
        'party_selected': party_id or '',
        'date_from': date_from or '',
        'date_to': date_to or '',
        'status_selected': status or '',
        'total_sum': total_sum,
    })


@login_required
def credit_note_list(request):
    cns = CreditNote.objects.filter(company=request.user.company).order_by('-issue_date')
    return render(request, 'billing/credit_note_list.html', {'credit_notes': cns})


@login_required
@role_required('vente')
def credit_note_create(request):
    def formset_factory_with_user(user):
        BaseFS = formset_factory(DocumentLineForm, extra=1, can_delete=False)
        class UserBoundFormSet(BaseFS):
            def _construct_form(self, i, **kwargs):
                kwargs['user'] = user
                return super()._construct_form(i, **kwargs)
        return UserBoundFormSet
    LineFormSet = formset_factory_with_user(request.user)
    if request.method == 'POST':
        form = CreditNoteForm(request.POST, user=request.user)
        formset = LineFormSet(request.POST, prefix='lines')
        if form.is_valid() and formset.is_valid():
            cn = form.save(commit=False)
            cn.company = request.user.company
            cn.sequence_code = 'AVOIR'
            cn.number = f"AVOIR-DRAFT-{uuid.uuid4().hex[:8]}"
            cn.save()
            any_line = False
            for lf in formset:
                if lf.cleaned_data:
                    line = lf.save(commit=False)
                    cn.lines.create(
                        product=line.product,
                        description=line.description,
                        quantity=line.quantity,
                        unit_price_ht=line.unit_price_ht,
                        discount_percent=line.discount_percent,
                        tax_rate=line.tax_rate,
                    )
                    any_line = True
            if not any_line:
                messages.error(request, "Veuillez ajouter au moins une ligne valide.")
                return render(request, 'billing/credit_note_form.html', {'form': form, 'formset': formset})
            cn.calculate_totals()
            year = datetime.now().year
            cn.number = f"AVOIR-{year}-{cn.id:04d}"
            cn.save()
            messages.success(request, f"Avoir {cn.number} créé avec succès.")
            return redirect('billing:credit_note_detail', pk=cn.pk)
        else:
            messages.error(request, "Formulaire invalide. Vérifiez les champs en rouge.")
    else:
        form = CreditNoteForm(user=request.user)
        formset = LineFormSet(prefix='lines')
    return render(request, 'billing/credit_note_form.html', {'form': form, 'formset': formset})


@login_required
def credit_note_detail(request, pk):
    cn = get_object_or_404(CreditNote, pk=pk, company=request.user.company)
    return render(request, 'billing/credit_note_detail.html', {'credit_note': cn})


@login_required
def credit_note_pdf(request, pk):
    cn = get_object_or_404(CreditNote, pk=pk, company=request.user.company)
    lines = cn.lines.all()
    company = request.user.company
    logo_src = None
    try:
        if getattr(company, 'logo', None) and company.logo:
            logo_src = company.logo.path
    except Exception:
        logo_src = None
    try:
        detail_url = request.build_absolute_uri(reverse('billing:credit_note_detail', args=[cn.pk]))
        qr_data_uri = generate_qr_data_uri(detail_url)
    except Exception:
        qr_data_uri = None

    html = render_to_string(
        'billing/pdf/credit_note_pdf.html',
        {
            'credit_note': cn,
            'lines': lines,
            'company': company,
            'logo_src': logo_src,
            'qr_data_uri': qr_data_uri,
        },
        request=request,
    )
    pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="AVOIR-{cn.number}.pdf"'
    return response


class QuoteListView(LoginRequiredMixin, ListView):
    model = Quote
    template_name = 'billing/quote_list.html'
    context_object_name = 'quotes'
    def get_queryset(self):
        return Quote.objects.filter(company=self.request.user.company).order_by('-issue_date')


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    def get_queryset(self):
        return Invoice.objects.filter(company=self.request.user.company).order_by('-issue_date')


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'billing/payment_list.html'
    context_object_name = 'payments'
    def get_queryset(self):
        return Payment.objects.filter(company=self.request.user.company).order_by('-date')


@login_required
def product_price(request):
    from catalog.models import Product
    # Déterminer l'index du formset et le product_id
    index = request.GET.get('index')
    product_id = request.GET.get('product')
    product_key = None
    if not product_id:
        for key, value in request.GET.items():
            if key.endswith('-product') and value:
                product_key = key
                product_id = value
                break
    if index is None and product_key:
        # product_key format: lines-<index>-product
        try:
            parts = product_key.split('-')
            if len(parts) >= 3 and parts[0] == 'lines' and parts[2] == 'product':
                index = parts[1]
        except Exception:
            index = ''
    description = ''
    unit_price = ''
    if product_id:
        try:
            product = Product.objects.get(pk=product_id, company=request.user.company)
            unit_price = f"{product.price_ht}"
            description = product.description or ''
        except Product.DoesNotExist:
            unit_price = ''
            description = ''
    return render(
        request,
        'billing/fragments/product_autofill.html',
        {
            'index': index or '',
            'unit_price': unit_price,
            'description': description,
        },
    )


@login_required
def quote_pdf(request, pk):
    quote = get_object_or_404(Quote, pk=pk, company=request.user.company)
    lines = quote.lines.all()
    company = request.user.company
    logo_src = None
    try:
        if getattr(company, 'logo', None) and company.logo:
            logo_src = company.logo.path
    except Exception:
        logo_src = None
    # Build QR pointing to this document's detail URL
    try:
        detail_url = request.build_absolute_uri(reverse('billing:quote_detail', args=[quote.pk]))
        qr_data_uri = generate_qr_data_uri(detail_url)
    except Exception:
        qr_data_uri = None

    html = render_to_string(
        'billing/pdf/quote_pdf.html',
        {
            'quote': quote,
            'lines': lines,
            'company': company,
            'logo_src': logo_src,
            'qr_data_uri': qr_data_uri,
        },
        request=request,
    )
    pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Devis-{quote.number}.pdf"'
    return response


@login_required
def purchase_order_pdf(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    lines = po.lines.all()
    company = request.user.company
    logo_src = None
    try:
        if getattr(company, 'logo', None) and company.logo:
            logo_src = company.logo.path
    except Exception:
        logo_src = None
    try:
        detail_url = request.build_absolute_uri(reverse('billing:purchase_order_detail', args=[po.pk]))
        qr_data_uri = generate_qr_data_uri(detail_url)
    except Exception:
        qr_data_uri = None

    html = render_to_string(
        'billing/pdf/purchase_order_pdf.html',
        {
            'po': po,
            'lines': lines,
            'company': company,
            'logo_src': logo_src,
            'qr_data_uri': qr_data_uri,
        },
        request=request,
    )
    pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="BC-{po.number}.pdf"'
    return response


@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)
    lines = invoice.lines.all()
    company = request.user.company
    logo_src = None
    try:
        if getattr(company, 'logo', None) and company.logo:
            logo_src = company.logo.path
    except Exception:
        logo_src = None
    try:
        detail_url = request.build_absolute_uri(reverse('billing:invoice_detail', args=[invoice.pk]))
        qr_data_uri = generate_qr_data_uri(detail_url)
    except Exception:
        qr_data_uri = None

    html = render_to_string(
        'billing/pdf/invoice_pdf.html',
        {
            'invoice': invoice,
            'lines': lines,
            'company': company,
            'logo_src': logo_src,
            'qr_data_uri': qr_data_uri,
        },
        request=request,
    )
    pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="FACTURE-{invoice.number}.pdf"'
    return response


@login_required
@role_required('vente')
def purchase_order_create(request):
    LineFormSet = formset_factory(DocumentLineForm, extra=1, can_delete=False)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        formset = LineFormSet(request.POST, prefix='lines')
        if form.is_valid() and formset.is_valid():
            po = form.save(commit=False)
            po.company = request.user.company
            po.sequence_code = 'BC'
            po.number = f"BC-DRAFT-{uuid.uuid4().hex[:8]}"
            po.save()
            any_line = False
            for lf in formset:
                if lf.cleaned_data:
                    line = lf.save(commit=False)
                    po.lines.create(
                        product=line.product,
                        description=line.description,
                        quantity=line.quantity,
                        unit_price_ht=line.unit_price_ht,
                        discount_percent=line.discount_percent,
                        tax_rate=line.tax_rate,
                    )
                    any_line = True
            if not any_line:
                messages.error(request, "Veuillez ajouter au moins une ligne valide.")
                return render(request, 'billing/purchase_order_form.html', {'form': form, 'formset': formset})
            po.calculate_totals()
            year = datetime.now().year
            po.number = f"BC-{year}-{po.id:04d}"
            po.save()
            # Create approval request if needed and enabled
            if request.user.company.get_preference('feature_approvals_enabled', True):
                try:
                    workflows = ApprovalWorkflow.objects.filter(
                        company=po.company, document_type='purchase_order', active=True
                    )
                    for wf in workflows:
                        needs_amount = bool(wf.amount_threshold and po.total_ttc and po.total_ttc >= wf.amount_threshold)
                        if needs_amount:
                            ar = ApprovalRequest.objects.create(
                                workflow=wf,
                                document_type='purchase_order',
                                document_id=po.id,
                                amount=po.total_ttc,
                                current_level=1,
                                total_levels=len(wf.approval_levels or []),
                                company=po.company,
                                created_by=request.user,
                            )
                            try:
                                Notification.create_notification(
                                    user=request.user,
                                    title='Approbation requise - Bon de commande',
                                    message=f"BC {po.number}: approbation requise.",
                                    notification_type='approval',
                                    priority='normal',
                                    action_url=reverse('billing:purchase_order_detail', args=[po.pk]),
                                    action_text='Voir le BC',
                                    company=po.company,
                                    created_by=request.user,
                                )
                            except Exception:
                                pass
                            messages.info(request, "Demande d'approbation créée pour ce BC.")
                            break
                except Exception:
                    pass
            messages.success(request, f"Bon de commande {po.number} créé avec succès.")
            return redirect('billing:purchase_order_detail', pk=po.pk)
        else:
            messages.error(request, "Formulaire invalide. Vérifiez les champs en rouge.")
    else:
        from django.utils import timezone
        form = PurchaseOrderForm(initial={'delivery_date': timezone.now().date()})
        formset = LineFormSet(prefix='lines')
    return render(request, 'billing/purchase_order_form.html', {'form': form, 'formset': formset})
