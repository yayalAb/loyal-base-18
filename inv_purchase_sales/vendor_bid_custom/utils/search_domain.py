from typing import List, Tuple
from odoo.api import Environment

def get_rfp_general_search_domain(env: Environment) -> List[Tuple[str, str, str]]:
    """
    Returns the general search domain for RFP based on user
    """
    domain = []
    if hasattr(env.user, 'partner_id') and env.user.partner_id.supplier_rank > 0:
        # Supplier: can see all approved RFPs
        domain.append(('state', '=', 'approved'))
        # 🚫 removed product_category restriction
    elif env.user.has_group('VendorBid.group_supplies_requester'):
        # If the user is a requester, filter by the rfp requested by them
        domain.append(('create_uid', '=', env.user.id))
    return domain
