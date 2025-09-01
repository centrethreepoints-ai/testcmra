"""
Advanced search functionality for the CRM system.
"""

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.contrib.contenttypes.models import ContentType


class AdvancedSearch:
    """Classe pour la recherche avancée dans le système."""
    
    @staticmethod
    def search_parties(query, company, filters=None):
        """
        Recherche avancée dans les parties (clients/fournisseurs).
        
        Args:
            query (str): Terme de recherche
            company: Société pour filtrer les résultats
            filters (dict): Filtres additionnels (is_customer, is_supplier, etc.)
        
        Returns:
            QuerySet: Résultats de la recherche
        """
        from crm.models import Party
        
        # Créer le vecteur de recherche
        search_vector = SearchVector('name', weight='A') + \
                       SearchVector('email', weight='B') + \
                       SearchVector('phone', weight='B') + \
                       SearchVector('mobile', weight='B') + \
                       SearchVector('billing_address', weight='C') + \
                       SearchVector('city', weight='C') + \
                       SearchVector('ice', weight='D') + \
                       SearchVector('if_field', weight='D') + \
                       SearchVector('rc', weight='D')
        
        # Créer la requête de recherche
        search_query = SearchQuery(query, config='french')
        
        # Recherche de base
        parties = Party.objects.filter(company=company)
        
        # Appliquer les filtres
        if filters:
            if filters.get('is_customer') is not None:
                parties = parties.filter(is_customer=filters['is_customer'])
            if filters.get('is_supplier') is not None:
                parties = parties.filter(is_supplier=filters['is_supplier'])
            if filters.get('city'):
                parties = parties.filter(city__icontains=filters['city'])
            if filters.get('country'):
                parties = parties.filter(country__icontains=filters['country'])
        
        # Recherche avec ranking
        parties = parties.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank', 'name')
        
        return parties
    
    @staticmethod
    def search_products(query, company, filters=None):
        """
        Recherche avancée dans les produits/services.
        
        Args:
            query (str): Terme de recherche
            company: Société pour filtrer les résultats
            filters (dict): Filtres additionnels (category, product_type, etc.)
        
        Returns:
            QuerySet: Résultats de la recherche
        """
        from catalog.models import Product
        
        # Créer le vecteur de recherche
        search_vector = SearchVector('name', weight='A') + \
                       SearchVector('description', weight='B') + \
                       SearchVector('sku', weight='C') + \
                       SearchVector('barcode', weight='C')
        
        # Créer la requête de recherche
        search_query = SearchQuery(query, config='french')
        
        # Recherche de base
        products = Product.objects.filter(company=company)
        
        # Appliquer les filtres
        if filters:
            if filters.get('category'):
                products = products.filter(category=filters['category'])
            if filters.get('product_type'):
                products = products.filter(product_type=filters['product_type'])
            if filters.get('active') is not None:
                products = products.filter(active=filters['active'])
            if filters.get('has_stock') is not None:
                products = products.filter(has_stock=filters['has_stock'])
            if filters.get('min_price'):
                products = products.filter(price_ht__gte=filters['min_price'])
            if filters.get('max_price'):
                products = products.filter(price_ht__lte=filters['max_price'])
        
        # Recherche avec ranking
        products = products.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank', 'name')
        
        return products
    
    @staticmethod
    def search_invoices(query, company, filters=None):
        """
        Recherche avancée dans les factures.
        
        Args:
            query (str): Terme de recherche
            company: Société pour filtrer les résultats
            filters (dict): Filtres additionnels (invoice_type, status, etc.)
        
        Returns:
            QuerySet: Résultats de la recherche
        """
        from billing.models import Invoice
        
        # Créer le vecteur de recherche
        search_vector = SearchVector('number', weight='A') + \
                       SearchVector('party__name', weight='B') + \
                       SearchVector('notes', weight='C')
        
        # Créer la requête de recherche
        search_query = SearchQuery(query, config='french')
        
        # Recherche de base
        invoices = Invoice.objects.filter(company=company)
        
        # Appliquer les filtres
        if filters:
            if filters.get('invoice_type'):
                invoices = invoices.filter(invoice_type=filters['invoice_type'])
            if filters.get('status'):
                invoices = invoices.filter(status=filters['status'])
            if filters.get('date_from'):
                invoices = invoices.filter(issue_date__gte=filters['date_from'])
            if filters.get('date_to'):
                invoices = invoices.filter(issue_date__lte=filters['date_to'])
            if filters.get('min_amount'):
                invoices = invoices.filter(total_ttc__gte=filters['min_amount'])
            if filters.get('max_amount'):
                invoices = invoices.filter(total_ttc__lte=filters['max_amount'])
        
        # Recherche avec ranking
        invoices = invoices.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank', '-issue_date')
        
        return invoices
    
    @staticmethod
    def search_quotes(query, company, filters=None):
        """
        Recherche avancée dans les devis.
        
        Args:
            query (str): Terme de recherche
            company: Société pour filtrer les résultats
            filters (dict): Filtres additionnels (status, validity_days, etc.)
        
        Returns:
            QuerySet: Résultats de la recherche
        """
        from billing.models import Quote
        
        # Créer le vecteur de recherche
        search_vector = SearchVector('number', weight='A') + \
                       SearchVector('party__name', weight='B') + \
                       SearchVector('notes', weight='C')
        
        # Créer la requête de recherche
        search_query = SearchQuery(query, config='french')
        
        # Recherche de base
        quotes = Quote.objects.filter(company=company)
        
        # Appliquer les filtres
        if filters:
            if filters.get('status'):
                quotes = quotes.filter(status=filters['status'])
            if filters.get('validity_days'):
                quotes = quotes.filter(validity_days=filters['validity_days'])
            if filters.get('is_converted') is not None:
                quotes = quotes.filter(is_converted=filters['is_converted'])
            if filters.get('date_from'):
                quotes = quotes.filter(issue_date__gte=filters['date_from'])
            if filters.get('date_to'):
                quotes = quotes.filter(issue_date__lte=filters['date_to'])
        
        # Recherche avec ranking
        quotes = quotes.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank', '-issue_date')
        
        return quotes
    
    @staticmethod
    def search_purchase_orders(query, company, filters=None):
        """
        Recherche avancée dans les bons de commande.
        
        Args:
            query (str): Terme de recherche
            company: Société pour filtrer les résultats
            filters (dict): Filtres additionnels (order_type, status, etc.)
        
        Returns:
            QuerySet: Résultats de la recherche
        """
        from billing.models import PurchaseOrder
        
        # Créer le vecteur de recherche
        search_vector = SearchVector('number', weight='A') + \
                       SearchVector('party__name', weight='B') + \
                       SearchVector('delivery_address', weight='C') + \
                       SearchVector('notes', weight='C')
        
        # Créer la requête de recherche
        search_query = SearchQuery(query, config='french')
        
        # Recherche de base
        pos = PurchaseOrder.objects.filter(company=company)
        
        # Appliquer les filtres
        if filters:
            if filters.get('order_type'):
                pos = pos.filter(order_type=filters['order_type'])
            if filters.get('status'):
                pos = pos.filter(status=filters['status'])
            if filters.get('date_from'):
                pos = pos.filter(issue_date__gte=filters['date_from'])
            if filters.get('date_to'):
                pos = pos.filter(issue_date__lte=filters['date_to'])
        
        # Recherche avec ranking
        pos = pos.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank', '-issue_date')
        
        return pos
    
    @staticmethod
    def search_payments(query, company, filters=None):
        """
        Recherche avancée dans les paiements.
        
        Args:
            query (str): Terme de recherche
            company: Société pour filtrer les résultats
            filters (dict): Filtres additionnels (method, payment_type, etc.)
        
        Returns:
            QuerySet: Résultats de la recherche
        """
        from billing.models import Payment
        
        # Créer le vecteur de recherche
        search_vector = SearchVector('reference', weight='A') + \
                       SearchVector('party__name', weight='B') + \
                       SearchVector('check_number', weight='C') + \
                       SearchVector('bank_name', weight='C') + \
                       SearchVector('notes', weight='C')
        
        # Créer la requête de recherche
        search_query = SearchQuery(query, config='french')
        
        # Recherche de base
        payments = Payment.objects.filter(company=company)
        
        # Appliquer les filtres
        if filters:
            if filters.get('method'):
                payments = payments.filter(method=filters['method'])
            if filters.get('payment_type'):
                payments = payments.filter(payment_type=filters['payment_type'])
            if filters.get('is_reconciled') is not None:
                payments = payments.filter(is_reconciled=filters['is_reconciled'])
            if filters.get('date_from'):
                payments = payments.filter(date__gte=filters['date_from'])
            if filters.get('date_to'):
                payments = payments.filter(date__lte=filters['date_to'])
            if filters.get('min_amount'):
                payments = payments.filter(amount__gte=filters['min_amount'])
            if filters.get('max_amount'):
                payments = payments.filter(amount__lte=filters['max_amount'])
        
        # Recherche avec ranking
        payments = payments.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank', '-date')
        
        return payments
    
    @staticmethod
    def search_journal_entries(query, company, filters=None):
        """
        Recherche avancée dans les écritures comptables.
        
        Args:
            query (str): Terme de recherche
            company: Société pour filtrer les résultats
            filters (dict): Filtres additionnels (journal, posted, etc.)
        
        Returns:
            QuerySet: Résultats de la recherche
        """
        from accounting.models import Move
        
        # Créer le vecteur de recherche
        search_vector = SearchVector('number', weight='A') + \
                       SearchVector('description', weight='B') + \
                       SearchVector('journal__name', weight='C')
        
        # Créer la requête de recherche
        search_query = SearchQuery(query, config='french')
        
        # Recherche de base
        moves = Move.objects.filter(company=company)
        
        # Appliquer les filtres
        if filters:
            if filters.get('journal'):
                moves = moves.filter(journal=filters['journal'])
            if filters.get('posted') is not None:
                moves = moves.filter(posted=filters['posted'])
            if filters.get('date_from'):
                moves = moves.filter(date__gte=filters['date_from'])
            if filters.get('date_to'):
                moves = moves.filter(date__lte=filters['date_to'])
        
        # Recherche avec ranking
        moves = moves.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank', '-date')
        
        return moves
    
    @staticmethod
    def global_search(query, company, models=None, limit=50):
        """
        Recherche globale dans tous les modèles principaux.
        
        Args:
            query (str): Terme de recherche
            company: Société pour filtrer les résultats
            models (list): Liste des modèles à inclure (None = tous)
            limit (int): Nombre maximum de résultats par modèle
        
        Returns:
            dict: Résultats groupés par modèle
        """
        results = {}
        
        # Définir les modèles par défaut si aucun spécifié
        if models is None:
            models = ['parties', 'products', 'invoices', 'quotes', 'payments']
        
        # Recherche dans les parties
        if 'parties' in models:
            parties = AdvancedSearch.search_parties(query, company)[:limit]
            if parties.exists():
                results['parties'] = {
                    'model_name': 'Parties',
                    'results': parties,
                    'count': parties.count()
                }
        
        # Recherche dans les produits
        if 'products' in models:
            products = AdvancedSearch.search_products(query, company)[:limit]
            if products.exists():
                results['products'] = {
                    'model_name': 'Produits',
                    'results': products,
                    'count': products.count()
                }
        
        # Recherche dans les factures
        if 'invoices' in models:
            invoices = AdvancedSearch.search_invoices(query, company)[:limit]
            if invoices.exists():
                results['invoices'] = {
                    'model_name': 'Factures',
                    'results': invoices,
                    'count': invoices.count()
                }
        
        # Recherche dans les devis
        if 'quotes' in models:
            quotes = AdvancedSearch.search_quotes(query, company)[:limit]
            if quotes.exists():
                results['quotes'] = {
                    'model_name': 'Devis',
                    'results': quotes,
                    'count': quotes.count()
                }
        
        # Recherche dans les paiements
        if 'payments' in models:
            payments = AdvancedSearch.search_payments(query, company)[:limit]
            if payments.exists():
                results['payments'] = {
                    'model_name': 'Paiements',
                    'results': payments,
                    'count': payments.count()
                }
        
        # Recherche dans les écritures comptables
        if 'journal_entries' in models:
            moves = AdvancedSearch.search_journal_entries(query, company)[:limit]
            if moves.exists():
                results['journal_entries'] = {
                    'model_name': 'Écritures comptables',
                    'results': moves,
                    'count': moves.count()
                }
        
        return results


class SearchSuggestion:
    """Classe pour les suggestions de recherche."""
    
    @staticmethod
    def get_party_suggestions(query, company, limit=10):
        """Obtenir des suggestions pour les parties."""
        from crm.models import Party
        
        if len(query) < 2:
            return Party.objects.none()
        
        return Party.objects.filter(
            company=company,
            name__icontains=query
        ).values_list('name', flat=True)[:limit]
    
    @staticmethod
    def get_product_suggestions(query, company, limit=10):
        """Obtenir des suggestions pour les produits."""
        from catalog.models import Product
        
        if len(query) < 2:
            return Product.objects.none()
        
        return Product.objects.filter(
            company=company,
            name__icontains=query
        ).values_list('name', flat=True)[:limit]
    
    @staticmethod
    def get_invoice_suggestions(query, company, limit=10):
        """Obtenir des suggestions pour les factures."""
        from billing.models import Invoice
        
        if len(query) < 2:
            return Invoice.objects.none()
        
        return Invoice.objects.filter(
            company=company,
            number__icontains=query
        ).values_list('number', flat=True)[:limit]
