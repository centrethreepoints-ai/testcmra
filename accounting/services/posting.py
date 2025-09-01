from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from accounting.models import Move, MoveLine, Journal, Account


def get_or_create_pcm_accounts(company):
    """Créer quelques comptes PCM minimaux si absents (clients 411, ventes 7xx, TVA 4457, banque 512)."""
    defaults = [
        ('411000', 'Clients', 'receivable'),
        ('401000', 'Fournisseurs', 'payable'),
        ('445700', 'TVA collectée', 'tax'),
        ('445660', 'TVA déductible', 'tax'),
        ('700000', 'Ventes', 'income'),
        ('600000', 'Achats', 'expense'),
        ('512000', 'Banque', 'bank'),
        ('530000', 'Caisse', 'cash'),
    ]
    created_map = {}
    for code, name, acc_type in defaults:
        acc, _ = Account.objects.get_or_create(company=company, code=code, defaults={'name': name, 'account_type': acc_type})
        created_map[code] = acc
    return created_map


def post_customer_invoice(company, invoice):
    """Comptabiliser une facture client (VENTES)."""
    accounts = get_or_create_pcm_accounts(company)
    journal, _ = Journal.objects.get_or_create(company=company, code='VEN', defaults={'name': 'Ventes', 'journal_type': 'VEN'})

    move = Move.objects.create(
        company=company,
        journal=journal,
        date=timezone.now().date(),
        ref=invoice.number,
        description=f"Facture client {invoice.number}",
        origin_type=ContentType.objects.get_for_model(invoice.__class__),
        origin_id=invoice.pk,
    )

    # Débit 411 Clients = Total TTC
    MoveLine.objects.create(
        move=move,
        account=accounts['411000'],
        party=invoice.party,
        label=f"Client {invoice.party.name}",
        debit=invoice.total_ttc,
        credit=Decimal('0.00'),
    )
    # Crédit 7xx Ventes = Total HT
    MoveLine.objects.create(
        move=move,
        account=accounts['700000'],
        party=invoice.party,
        label="Ventes",
        debit=Decimal('0.00'),
        credit=invoice.total_ht,
    )
    # Crédit 4457 TVA collectée = TVA
    if invoice.total_tva and invoice.total_tva > 0:
        MoveLine.objects.create(
            move=move,
            account=accounts['445700'],
            party=invoice.party,
            label="TVA collectée",
            debit=Decimal('0.00'),
            credit=invoice.total_tva,
        )

    recompute_totals(move)
    move.post()
    return move


def post_supplier_invoice(company, invoice):
    """Comptabiliser une facture fournisseur (ACHATS)."""
    accounts = get_or_create_pcm_accounts(company)
    journal, _ = Journal.objects.get_or_create(company=company, code='ACH', defaults={'name': 'Achats', 'journal_type': 'ACH'})

    move = Move.objects.create(
        company=company,
        journal=journal,
        date=timezone.now().date(),
        ref=invoice.number,
        description=f"Facture fournisseur {invoice.number}",
        origin_type=ContentType.objects.get_for_model(invoice.__class__),
        origin_id=invoice.pk,
    )

    # Débit 6xx Achats = Total HT
    MoveLine.objects.create(
        move=move,
        account=accounts['600000'],
        party=invoice.party,
        label="Achats",
        debit=invoice.total_ht,
        credit=Decimal('0.00'),
    )
    # Débit 44566 TVA déductible = TVA
    if invoice.total_tva and invoice.total_tva > 0:
        MoveLine.objects.create(
            move=move,
            account=accounts['445660'],
            party=invoice.party,
            label="TVA déductible",
            debit=invoice.total_tva,
            credit=Decimal('0.00'),
        )
    # Crédit 401 Fournisseurs = Total TTC
    MoveLine.objects.create(
        move=move,
        account=accounts['401000'],
        party=invoice.party,
        label=f"Fournisseur {invoice.party.name}",
        debit=Decimal('0.00'),
        credit=invoice.total_ttc,
    )

    recompute_totals(move)
    move.post()
    return move


def post_payment_on_invoice(company, invoice, amount, method='bank'):
    """Comptabiliser un encaissement client (banque/caisse) contre facture."""
    accounts = get_or_create_pcm_accounts(company)
    journal_code = 'BQ' if method == 'bank' else 'CAI'
    journal_name = 'Banque' if method == 'bank' else 'Caisse'
    journal, _ = Journal.objects.get_or_create(company=company, code=journal_code, defaults={'name': journal_name, 'journal_type': journal_code})

    move = Move.objects.create(
        company=company,
        journal=journal,
        date=timezone.now().date(),
        ref=f"PAY-{invoice.number}",
        description=f"Paiement facture {invoice.number}",
        origin_type=ContentType.objects.get_for_model(invoice.__class__),
        origin_id=invoice.pk,
    )

    # Débit banque/caisse
    MoveLine.objects.create(
        move=move,
        account=accounts['512000'] if method == 'bank' else accounts['530000'],
        party=invoice.party,
        label="Encaissement",
        debit=amount,
        credit=Decimal('0.00'),
    )
    # Crédit 411 Clients
    MoveLine.objects.create(
        move=move,
        account=accounts['411000'],
        party=invoice.party,
        label="Client",
        debit=Decimal('0.00'),
        credit=amount,
    )

    recompute_totals(move)
    move.post()
    return move


def recompute_totals(move: Move):
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    for line in move.lines.all():
        total_debit += line.debit
        total_credit += line.credit
    move.total_debit = total_debit
    move.total_credit = total_credit
    move.save(update_fields=['total_debit', 'total_credit'])
