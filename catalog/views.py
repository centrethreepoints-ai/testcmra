"""
Views for catalog application.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Q, F
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from decimal import Decimal
from django.http import HttpResponse
from datetime import timedelta

from .models import Product, Category, TaxRate, StockMovement, ProductStock, InventorySession, InventoryCount


@login_required
def product_list(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé au catalogue.')
        return redirect('core:dashboard')
    company = request.user.company
    
    # Get all products with related data
    products = Product.objects.filter(company=company).select_related(
        'category', 'tax_rate'
    ).order_by('name')
    
    # Calculate total stock value
    total_value = sum(
        product.price_ht * getattr(product, 'current_stock', 0) 
        for product in products 
        if product.product_type != 'service'
    )
    
    context = {
        'products': products,
        'total_value': total_value,
    }
    
    return render(request, 'catalog/product_list.html', context)


@login_required
def product_detail(request, pk):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé au catalogue.')
        return redirect('core:dashboard')
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    stock_movements = product.stock_movements.all()[:10]  # Last 10 movements
    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'stock_movements': stock_movements
    })


@login_required
def category_list(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    from django.db.models import Q
    categories = list(
        Category.objects.filter(
            Q(company=request.user.company) | Q(company__isnull=True)
        ).select_related('parent')
    )
    # Prepare tree structure: attach children to each category instance
    by_id = {c.id: c for c in categories}
    for c in categories:
        setattr(c, 'tree_children', [])
    roots = []
    # Detect cycles by walking ancestor chain
    has_cycle = False
    total = len(categories)
    for c in categories:
        seen = set()
        cur = c
        steps = 0
        while cur and cur.parent_id:
            if cur.parent_id in seen:
                has_cycle = True
                break
            seen.add(cur.parent_id)
            cur = by_id.get(cur.parent_id)
            steps += 1
            if steps > total:
                has_cycle = True
                break
        if has_cycle:
            break

    for c in categories:
        parent_in_set = c.parent_id in by_id if c.parent_id else False
        if c.parent_id and parent_in_set:
            by_id[c.parent_id].tree_children.append(c)
        else:
            roots.append(c)

    def sort_branch(nodes):
        nodes.sort(key=lambda x: (x.name or '').lower())
        for n in nodes:
            sort_branch(getattr(n, 'tree_children', []))
    sort_branch(roots)

    if has_cycle and roots:
        try:
            messages.error(request, "Cycle de catégories détecté. L'arborescence peut être incomplète.")
        except Exception:
            pass
    if has_cycle and not roots:
        try:
            messages.error(request, "Cycle de catégories détecté. Affichage hiérarchique indisponible.")
        except Exception:
            pass
    context = {'roots': roots, 'has_cycle': has_cycle}
    return render(request, 'catalog/category_list.html', context)


@login_required
def category_create(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    # Liste des catégories existantes pour choisir un parent
    parent_choices = Category.objects.filter(company=request.user.company).order_by('name')
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        description = (request.POST.get('description') or '').strip()
        parent_id = request.POST.get('parent') or None
        errors = []
        if not name:
            errors.append('Le nom est requis.')
        # Unicité par société (insensible à la casse pour l'UX)
        if name and Category.objects.filter(company=request.user.company, name__iexact=name).exists():
            errors.append('Une catégorie avec ce nom existe déjà.')
        # Valider le parent
        parent_obj = None
        if parent_id:
            try:
                parent_obj = Category.objects.get(pk=int(parent_id), company=request.user.company)
            except Exception:
                errors.append("Catégorie parente invalide.")
        if errors:
            for e in errors:
                messages.error(request, e)
            # Repasser les valeurs au formulaire
            preview = Category(name=name, description=description, parent=parent_obj, company=request.user.company)
            return render(request, 'catalog/category_form.html', {
                'category': preview,
                'categories': parent_choices,
            })
        # Créer la catégorie
        Category.objects.create(
            name=name,
            description=description,
            parent=parent_obj,
            company=request.user.company,
        )
        messages.success(request, 'Catégorie créée avec succès.')
        return redirect('catalog:category_list')
    return render(request, 'catalog/category_form.html', {'categories': parent_choices})


@login_required
def category_edit(request, pk):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    category = get_object_or_404(Category, pk=pk, company=request.user.company)
    parent_choices = Category.objects.filter(company=request.user.company).exclude(pk=category.pk).order_by('name')
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        description = (request.POST.get('description') or '').strip()
        parent_id = request.POST.get('parent') or None
        errors = []
        if not name:
            errors.append('Le nom est requis.')
        # Unicité par société, exclure l'objet courant
        if name and Category.objects.filter(company=request.user.company, name__iexact=name).exclude(pk=category.pk).exists():
            errors.append('Une autre catégorie avec ce nom existe déjà.')
        parent_obj = None
        if parent_id:
            try:
                pid = int(parent_id)
                if pid == category.pk:
                    errors.append('Une catégorie ne peut pas être son propre parent.')
                else:
                    parent_obj = Category.objects.get(pk=pid, company=request.user.company)
                    # Prevent selecting a descendant as parent (would create a cycle)
                    cursor = parent_obj
                    climbs = 0
                    while cursor and cursor.parent_id and climbs < 1000:
                        if cursor.parent_id == category.pk:
                            errors.append('Impossible de définir un descendant comme parent (cycle détecté).')
                            parent_obj = None
                            break
                        cursor = Category.objects.filter(pk=cursor.parent_id, company=request.user.company).first()
                        climbs += 1
            except Exception:
                errors.append('Catégorie parente invalide.')
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            category.name = name
            category.description = description
            category.parent = parent_obj
            category.company = request.user.company
            try:
                category.save()
                messages.success(request, 'Catégorie mise à jour avec succès.')
                return redirect('catalog:category_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'enregistrement: {e}")
    return render(request, 'catalog/category_form.html', {'category': category, 'categories': parent_choices})


@login_required
def category_delete(request, pk):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    category = get_object_or_404(Category, pk=pk, company=request.user.company)
    if request.method == 'POST':
        try:
            category.delete()
            messages.success(request, 'Catégorie supprimée avec succès.')
        except ProtectedError:
            messages.error(request, "Impossible de supprimer cette catégorie car elle est utilisée par des produits.")
        except Exception as e:
            messages.error(request, f"Suppression échouée: {e}")
        return redirect('catalog:category_list')
    return render(request, 'catalog/category_confirm_delete.html', {'object': category})


@login_required
def tax_rate_list(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    tax_rates = TaxRate.objects.filter(company=request.user.company).order_by('rate')
    return render(request, 'catalog/tax_rate_list.html', {'tax_rates': tax_rates})


@login_required
def tax_rate_create(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        raw_rate = (request.POST.get('rate') or '').strip()
        is_active_raw = (request.POST.get('is_active') or 'true').lower()
        description = (request.POST.get('description') or '').strip()
        code = (request.POST.get('code') or '').strip()
        errors = []
        if not name:
            errors.append('Le nom est requis.')
        from decimal import Decimal as D
        rate_val = None
        try:
            rate_val = D(raw_rate)
            if rate_val < 0:
                errors.append('Le taux ne peut pas être négatif.')
        except Exception:
            errors.append('Taux invalide.')
        if TaxRate.objects.filter(company=request.user.company, rate=rate_val).exists():
            errors.append('Un taux avec cette valeur existe déjà.')
        if errors:
            for e in errors:
                messages.error(request, e)
            preview = TaxRate(name=name, rate=rate_val or 0, is_active=(is_active_raw == 'true'), description=description, code=code)
            return render(request, 'catalog/tax_rate_form.html', {'tax_rate': preview})
        TaxRate.objects.create(
            name=name,
            rate=rate_val,
            is_active=(is_active_raw == 'true'),
            description=description or '',
            code=code or '',
            company=request.user.company,
        )
        messages.success(request, 'Taux créé avec succès.')
        return redirect('catalog:tax_rate_list')
    return render(request, 'catalog/tax_rate_form.html', {})


@login_required
def tax_rate_edit(request, pk):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    tax = get_object_or_404(TaxRate, pk=pk, company=request.user.company)
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        raw_rate = (request.POST.get('rate') or '').strip()
        is_active_raw = (request.POST.get('is_active') or 'true').lower()
        description = (request.POST.get('description') or '').strip()
        code = (request.POST.get('code') or '').strip()
        errors = []
        if not name:
            errors.append('Le nom est requis.')
        from decimal import Decimal as D
        rate_val = None
        try:
            rate_val = D(raw_rate)
            if rate_val < 0:
                errors.append('Le taux ne peut pas être négatif.')
        except Exception:
            errors.append('Taux invalide.')
        if rate_val is not None and TaxRate.objects.filter(company=request.user.company, rate=rate_val).exclude(pk=tax.pk).exists():
            errors.append('Un autre taux avec cette valeur existe déjà.')
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            tax.name = name
            tax.rate = rate_val
            tax.is_active = (is_active_raw == 'true')
            tax.description = description or ''
            tax.code = code or ''
            tax.company = request.user.company
            try:
                tax.save()
                messages.success(request, 'Taux mis à jour avec succès.')
                return redirect('catalog:tax_rate_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'enregistrement: {e}")
    return render(request, 'catalog/tax_rate_form.html', {'tax_rate': tax})


@login_required
def tax_rate_delete(request, pk):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    tax = get_object_or_404(TaxRate, pk=pk, company=request.user.company)
    if request.method == 'POST':
        # tax.delete()
        try:
            tax.delete()
            messages.success(request, 'Taux supprimé avec succès.')
        except Exception as e:
            messages.error(request, f'Suppression échouée: {e}')
        return redirect('catalog:tax_rate_list')
    return render(request, 'catalog/tax_rate_confirm_delete.html', {'object': tax})


# New Stock Management Views
@login_required
def stock_list(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    """Vue pour la liste des stocks."""
    company = request.user.company
    
    # Get all products with stock info
    products = Product.objects.filter(company=company).select_related('category', 'tax_rate')
    
    # Filter by stock status
    stock_status = request.GET.get('status', '')
    if stock_status == 'low':
        products = products.filter(has_stock=True, current_stock__lte=F('min_stock'))
    elif stock_status == 'out':
        products = products.filter(has_stock=True, current_stock=0)
    elif stock_status == 'normal':
        products = products.filter(has_stock=True, current_stock__gt=F('min_stock'))
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(sku__icontains=search_query) | 
            Q(barcode__icontains=search_query)
        )
    
    # Category filter
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    categories = Category.objects.filter(company=company)
    
    context = {
        'products': products,
        'categories': categories,
        'stock_status': stock_status,
        'search_query': search_query,
        'category_id': category_id,
        'total_products': products.count(),
        'low_stock_count': products.filter(has_stock=True, current_stock__lte=F('min_stock')).count(),
        'out_of_stock_count': products.filter(has_stock=True, current_stock=0).count(),
    }
    
    return render(request, 'catalog/stock_list.html', context)


@login_required
def stock_movements(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    """Vue pour l'historique des mouvements de stock."""
    company = request.user.company
    
    movements = StockMovement.objects.filter(company=company).select_related(
        'product', 'product__category', 'created_by'
    ).order_by('-created_at')
    
    # Filters
    movement_type = request.GET.get('type', '')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    product_id = request.GET.get('product', '')
    if product_id:
        movements = movements.filter(product_id=product_id)

    source = request.GET.get('source', '')
    if source == 'inventory':
        movements = movements.filter(reference_type='inventory')
    
    date_from = request.GET.get('date_from', '')
    if date_from:
        movements = movements.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to', '')
    if date_to:
        movements = movements.filter(created_at__date__lte=date_to)
    
    # Get products for filter dropdown
    products = Product.objects.filter(company=company, has_stock=True).order_by('name')
    
    context = {
        'movements': movements,
        'products': products,
        'movement_type': movement_type,
        'product_id': product_id,
        'source': source,
        'date_from': date_from,
        'date_to': date_to,
        'total_movements': movements.count(),
    }
    
    return render(request, 'catalog/stock_movements.html', context)


@login_required
def stock_movement_detail(request, pk):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    from .models import StockMovement
    movement = get_object_or_404(StockMovement.objects.select_related('product', 'product__category', 'created_by'), pk=pk, company=request.user.company)
    return render(request, 'catalog/fragments/stock_movement_detail.html', {
        'movement': movement
    })


@login_required
def low_stock_alerts(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    """Vue pour les alertes de stock bas."""
    company = request.user.company
    
    # Get products with low stock
    low_stock_products = Product.objects.filter(
        company=company,
        has_stock=True,
        current_stock__lte=F('min_stock')
    ).select_related('category')
    
    # Get out of stock products
    out_of_stock_products = Product.objects.filter(
        company=company,
        has_stock=True,
        current_stock=0
    ).select_related('category')
    
    context = {
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'low_stock_count': low_stock_products.count(),
        'out_of_stock_count': out_of_stock_products.count(),
    }
    
    return render(request, 'catalog/low_stock_alerts.html', context)


@login_required
def stock_adjustment(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    """Vue pour l'ajustement des stocks."""
    if request.method == 'POST':
        product_id = request.POST.get('product')
        movement_type = request.POST.get('movement_type')
        # Parse and validate inputs safely
        try:
            quantity = int(request.POST.get('quantity') or 0)
        except Exception:
            quantity = 0
        try:
            unit_cost = Decimal(str(request.POST.get('unit_cost') or '0'))
        except Exception:
            unit_cost = Decimal('0')
        reference = request.POST.get('reference', '')
        notes = request.POST.get('notes', '')
        
        try:
            product = Product.objects.get(pk=product_id, company=request.user.company)
            
            # Create stock movement with explicit stock_before
            StockMovement.objects.create(
                product=product,
                movement_type=movement_type,
                quantity=quantity,
                unit_cost=unit_cost,
                reference=reference,
                reference_type=(request.POST.get('reference_type') or 'adjustment'),
                stock_before=int(getattr(product, 'current_stock', 0) or 0),
                notes=notes,
                company=request.user.company,
                created_by=request.user
            )
            
            messages.success(request, f'Stock ajusté avec succès pour {product.name}')
            return redirect('catalog:stock_list')
            
        except Product.DoesNotExist:
            messages.error(request, 'Produit non trouvé')
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajustement: {str(e)}')
    
    # Get products with stock management enabled
    products = Product.objects.filter(
        company=request.user.company,
        has_stock=True
    ).order_by('name')
    
    return render(request, 'catalog/stock_adjustment.html', {'products': products})


@login_required
def inventory_list(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    company = request.user.company
    products = Product.objects.filter(company=company, has_stock=True).select_related('category').order_by('name')
    if request.method == 'POST':
        # Create a historical session capturing counts instead of adjusting stock
        now = timezone.now()
        name = f"Inventaire rapide {now.strftime('%d/%m/%Y %H:%M')}"
        session = InventorySession.objects.create(
            company=company,
            name=name,
            scope_type='all',
            is_blind=False,
            freeze_stock=False,
            tolerance_percent=Decimal('0.00'),
            status='closed',
            started_at=now,
            ended_at=now,
            created_by=request.user,
        )
        snapshot = {}
        to_create = []
        created_lines = 0
        for p in products:
            current_qty = int(getattr(p, 'current_stock', 0) or 0)
            snapshot[str(p.id)] = {
                'name': p.name,
                'category': getattr(p.category, 'name', ''),
                'qty': current_qty,
            }
            key = f"counted_{p.id}"
            counted_val = request.POST.get(key)
            counted = None
            if counted_val is not None and counted_val != '':
                try:
                    counted = int(counted_val)
                except Exception:
                    counted = None
            to_create.append(InventoryCount(
                session=session,
                product=p,
                snapshot_qty=current_qty,
                counted_qty=counted,
                status='counted' if counted is not None else 'pending',
            ))
            created_lines += 1
        InventoryCount.objects.bulk_create(to_create)
        session.snapshot = snapshot
        session.save(update_fields=['snapshot'])
        messages.success(request, f'Session d\'inventaire créée ({created_lines} lignes).')
        return redirect('catalog:inventory_session_detail', pk=session.pk)
    return render(request, 'catalog/inventory_list.html', {
        'products': products,
    })


@login_required
def inventory_session_list(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    sessions = InventorySession.objects.filter(company=request.user.company).order_by('-created_at')
    return render(request, 'catalog/inventory_session_list.html', {'sessions': sessions})


@login_required
def inventory_session_create(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    categories = Category.objects.filter(company=request.user.company).order_by('name')
    if request.method == 'POST':
        name = request.POST.get('name') or 'Inventaire'
        scope_type = request.POST.get('scope_type') or 'all'
        category_id = request.POST.get('category') or None
        is_blind = bool(request.POST.get('is_blind'))
        freeze_stock = bool(request.POST.get('freeze_stock'))
        from decimal import Decimal as D
        tolerance = D(request.POST.get('tolerance_percent') or '0')
        session = InventorySession.objects.create(
            company=request.user.company,
            name=name,
            scope_type=scope_type,
            category_id=category_id,
            is_blind=is_blind,
            freeze_stock=freeze_stock,
            tolerance_percent=tolerance,
            created_by=request.user,
        )
        messages.success(request, 'Session créée.')
        return redirect('catalog:inventory_session_detail', pk=session.pk)
    return render(request, 'catalog/inventory_session_form.html', {'categories': categories})


@login_required
def inventory_session_detail(request, pk):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    session = get_object_or_404(InventorySession, pk=pk, company=request.user.company)
    if request.method == 'POST' and session.status == 'active':
        # Persist counted quantities from form inputs: count_<count_id>
        updated = 0
        for cnt in session.counts.all():
            key = f"count_{cnt.id}"
            if key in request.POST:
                raw = request.POST.get(key) or ''
                try:
                    new_qty = int(raw)
                except Exception:
                    new_qty = None
                cnt.counted_qty = new_qty
                # Auto-flag outliers if tolerance provided
                if new_qty is None:
                    cnt.status = 'pending'
                else:
                    if session.tolerance_percent and cnt.snapshot_qty is not None:
                        try:
                            tol = float(session.tolerance_percent)
                            # percent of snapshot; if snapshot 0, any non-zero is outlier
                            base = float(cnt.snapshot_qty)
                            diff = abs(float(new_qty) - base)
                            outlier = (base == 0 and new_qty != 0) or (base != 0 and (diff / base * 100.0) > tol)
                        except Exception:
                            outlier = False
                        cnt.status = 'flagged' if outlier else 'counted'
                    else:
                        cnt.status = 'counted'
                cnt.save(update_fields=['counted_qty', 'status', 'updated_at'])
                updated += 1
        if updated:
            messages.success(request, f"{updated} lignes enregistrées.")
        return redirect('catalog:inventory_session_detail', pk=session.pk)
    counts = session.counts.select_related('product', 'product__category', 'assigned_to').order_by('product__name')
    progress = session.compute_progress()
    return render(request, 'catalog/inventory_session_detail.html', {
        'session': session,
        'counts': counts,
        'progress': progress,
    })


@login_required
def inventory_session_start(request, pk):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    session = get_object_or_404(InventorySession, pk=pk, company=request.user.company)
    if request.method == 'POST' and session.status == 'draft':
        from django.utils import timezone as djtz
        # Build snapshot and counts
        qs = Product.objects.filter(company=session.company, has_stock=True)
        if session.scope_type == 'category' and session.category_id:
            qs = qs.filter(category_id=session.category_id)
        snapshot = {}
        to_create = []
        for p in qs.select_related('category'):
            snapshot[str(p.id)] = {
                'name': p.name,
                'category': getattr(p.category, 'name', ''),
                'qty': int(getattr(p, 'current_stock', 0) or 0),
            }
            to_create.append(InventoryCount(
                session=session,
                product=p,
                snapshot_qty=int(getattr(p, 'current_stock', 0) or 0),
                status='pending',
            ))
        InventoryCount.objects.bulk_create(to_create)
        session.snapshot = snapshot
        session.status = 'active'
        session.started_at = djtz.now()
        session.save(update_fields=['snapshot', 'status', 'started_at'])
        messages.success(request, 'Session démarrée. Snapshot enregistré.')
    return redirect('catalog:inventory_session_detail', pk=session.pk)


@login_required
def inventory_session_close(request, pk):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    session = get_object_or_404(InventorySession, pk=pk, company=request.user.company)
    if request.method == 'POST' and session.status == 'active':
        from django.utils import timezone as djtz
        session.status = 'closed'
        session.ended_at = djtz.now()
        session.save(update_fields=['status', 'ended_at'])
        messages.success(request, 'Session clôturée.')
    return redirect('catalog:inventory_session_detail', pk=session.pk)


@login_required
def inventory_session_apply(request, pk):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    session = get_object_or_404(InventorySession, pk=pk, company=request.user.company)
    if request.method == 'POST' and session.status in ['active', 'closed']:
        from django.utils import timezone as djtz
        from decimal import Decimal as D
        applied = 0
        for cnt in session.counts.select_related('product').all():
            final_qty = cnt.recounted_qty if cnt.recounted_qty is not None else cnt.counted_qty
            if final_qty is None:
                continue
            product = cnt.product
            current = int(getattr(product, 'current_stock', 0) or 0)
            if final_qty == current:
                continue
            # Create adjustment movement to set stock to final_qty
            try:
                StockMovement.objects.create(
                    product=product,
                    movement_type='adjustment',
                    quantity=final_qty,
                    unit_cost=D(getattr(product, 'price_ht', D('0.00')) or 0),
                    reference=f'INV-{session.id}',
                    reference_type='inventory',
                    reference_id=session.id,
                    stock_before=current,
                    notes='Ajustement inventaire',
                    company=session.company,
                    created_by=request.user,
                )
                applied += 1
            except Exception:
                continue
        if session.status != 'closed':
            session.status = 'closed'
            session.ended_at = djtz.now()
            session.save(update_fields=['status', 'ended_at'])
        messages.success(request, f"Ajustements appliqués: {applied}")
    return redirect('catalog:inventory_session_detail', pk=session.pk)


@login_required
def inventory_export_csv(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    company = request.user.company
    products = Product.objects.filter(company=company, has_stock=True).select_related('category').order_by('name')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="inventaire.csv"'
    # Write BOM for Excel
    response.write('\ufeff')
    import csv
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID', 'Nom', 'Catégorie', 'Stock système', 'Compté'])
    for p in products:
        writer.writerow([p.id, p.name, getattr(p.category, 'name', ''), p.current_stock, ''])
    return response


@login_required
def inventory_import_csv(request):
    if request.user.role == 'comptable':
        messages.error(request, 'Accès non autorisé aux stocks.')
        return redirect('core:dashboard')
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            import csv, io
            file = request.FILES['file']
            decoded = io.TextIOWrapper(file.file, encoding='utf-8')
            reader = csv.DictReader(decoded, delimiter=';')
            # Build a dict id->counted
            counted_map = {}
            for row in reader:
                pid = int(row.get('ID') or 0)
                counted_val = row.get('Compté') or row.get('Compte') or row.get('counted') or ''
                try:
                    counted_map[pid] = int(counted_val)
                except Exception:
                    continue
            # Prepare context with products and prefilled counts
            company = request.user.company
            products = list(Product.objects.filter(company=company, has_stock=True).select_related('category').order_by('name'))
            for p in products:
                p.prefill_counted = counted_map.get(p.id)
            messages.success(request, 'Fichier importé. Les quantités comptées ont été pré-remplies.')
            return render(request, 'catalog/inventory_list.html', {'products': products})
        except Exception as e:
            messages.error(request, f'Echec import: {e}')
            return redirect('catalog:inventory_list')
    messages.error(request, 'Aucun fichier importé.')
    return redirect('catalog:inventory_list')


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    def get_queryset(self):
        return Product.objects.filter(company=self.request.user.company).order_by('name')


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'
    def get_queryset(self):
        return Product.objects.filter(company=self.request.user.company)


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    template_name = 'catalog/product_form.html'
    fields = ['name', 'description', 'category', 'product_type', 'price_ht', 'tax_rate', 'has_stock', 'current_stock', 'min_stock', 'max_stock', 'sku', 'barcode', 'is_active']
    success_url = reverse_lazy('catalog:product_list')
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter selectable data by current company
        form.fields['category'].queryset = Category.objects.filter(company=self.request.user.company).order_by('name')
        form.fields['tax_rate'].queryset = TaxRate.objects.filter(company=self.request.user.company, is_active=True).order_by('rate')
        # Make stock numeric fields optional and set sensible defaults
        if 'current_stock' in form.fields:
            form.fields['current_stock'].required = False
            form.fields['current_stock'].initial = 0
        if 'min_stock' in form.fields:
            form.fields['min_stock'].required = False
            form.fields['min_stock'].initial = 0
        if 'max_stock' in form.fields:
            form.fields['max_stock'].required = False
            form.fields['max_stock'].initial = 1000
        return form
    def form_valid(self, form):
        form.instance.company = self.request.user.company
        # Apply defaults if left blank
        try:
            if not form.cleaned_data.get('current_stock') and form.cleaned_data.get('current_stock') != 0:
                form.instance.current_stock = 0
        except Exception:
            form.instance.current_stock = 0
        try:
            if not form.cleaned_data.get('min_stock') and form.cleaned_data.get('min_stock') != 0:
                form.instance.min_stock = 0
        except Exception:
            form.instance.min_stock = 0
        try:
            if not form.cleaned_data.get('max_stock') and form.cleaned_data.get('max_stock') != 0:
                form.instance.max_stock = 1000
        except Exception:
            form.instance.max_stock = 1000
        try:
            messages.success(self.request, 'Produit créé avec succès.')
        except Exception:
            pass
        return super().form_valid(form)
    def form_invalid(self, form):
        try:
            from django.utils.html import format_html_join
            error_list = format_html_join('<br>', '{}: {}', ((f, ', '.join(e)) for f, e in form.errors.items()))
            messages.error(self.request, f'Formulaire invalide:<br>{error_list}')
        except Exception:
            messages.error(self.request, 'Formulaire invalide. Veuillez corriger les champs en rouge.')
        return super().form_invalid(form)


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    template_name = 'catalog/product_form.html'
    fields = ['name', 'description', 'category', 'product_type', 'price_ht', 'tax_rate', 'has_stock', 'current_stock', 'min_stock', 'max_stock', 'sku', 'barcode', 'is_active']
    success_url = reverse_lazy('catalog:product_list')
    def get_queryset(self):
        return Product.objects.filter(company=self.request.user.company)
    def form_valid(self, form):
        form.instance.company = self.request.user.company
        response = super().form_valid(form)
        try:
            messages.success(self.request, 'Produit mis à jour avec succès.')
        except Exception:
            pass
        return response
    def form_invalid(self, form):
        try:
            from django.utils.html import format_html_join
            error_list = format_html_join(', ', '{}: {}', ((f, ', '.join(e)) for f, e in form.errors.items()))
            messages.error(self.request, f'Formulaire invalide: {error_list}')
        except Exception:
            messages.error(self.request, 'Formulaire invalide.')
        return super().form_invalid(form)
    def get_success_url(self):
        return self.success_url
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Manual update to ensure persistence
        data = request.POST
        try:
            self.object.name = data.get('name', self.object.name)
            self.object.description = data.get('description', self.object.description)
            self.object.product_type = data.get('product_type', self.object.product_type) or self.object.product_type
            self.object.price_ht = data.get('price_ht', self.object.price_ht) or self.object.price_ht
            self.object.tax_rate_id = data.get('tax_rate') or None
            self.object.has_stock = bool(data.get('has_stock'))
            self.object.current_stock = int(data.get('current_stock') or self.object.current_stock or 0)
            self.object.min_stock = int(data.get('min_stock') or self.object.min_stock or 0)
            self.object.max_stock = int(data.get('max_stock') or self.object.max_stock or 0)
            self.object.sku = data.get('sku', self.object.sku)
            self.object.barcode = data.get('barcode', self.object.barcode)
            cat = data.get('category')
            self.object.category_id = int(cat) if cat else None
            self.object.is_active = bool(data.get('is_active') or data.get('is_active') == 'on')
            self.object.company = request.user.company
            self.object.save()
            try:
                messages.success(request, 'Produit mis à jour avec succès.')
            except Exception:
                pass
            return redirect(self.get_success_url())
        except Exception as e:
            try:
                messages.error(request, f"Erreur lors de l'enregistrement: {e}")
            except Exception:
                pass
            return super().post(request, *args, **kwargs)


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'catalog/product_confirm_delete.html'
    success_url = reverse_lazy('catalog:product_list')
    def get_queryset(self):
        return Product.objects.filter(company=self.request.user.company)


