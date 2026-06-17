from odoo import http, _
from odoo.http import request


class CustomMeasureController(http.Controller):

    @http.route(
        ['/custom_measure/quote'],
        type='http', auth='public', website=True,
        methods=['POST'], csrf=True)
    def custom_measure_quote(self, **post):
        """Reçoit les mesures saisies par le client et crée un devis (brouillon)."""
        env = request.env
        website = request.website

        # --- Produit -------------------------------------------------------
        try:
            tmpl_id = int(post.get('product_template_id'))
        except (TypeError, ValueError):
            return request.redirect('/shop')

        template = env['product.template'].sudo().browse(tmpl_id)
        if not template.exists() or not template.is_custom_measure:
            return request.redirect('/shop')

        product = template.product_variant_id
        if not product:
            return request.redirect('/shop')

        # --- Quantité ------------------------------------------------------
        try:
            qty = float(post.get('quantity') or 1)
        except ValueError:
            qty = 1.0
        if qty <= 0:
            qty = 1.0

        # --- Lecture / validation des mesures ------------------------------
        measures = []
        errors = []
        for mf in template.measure_field_ids:
            raw = (post.get('measure_%d' % mf.id) or '').strip()
            if not raw:
                if mf.required:
                    errors.append(_("Le champ « %s » est obligatoire.") % mf.name)
                continue
            if mf.field_type in ('float', 'integer'):
                try:
                    num = float(raw.replace(',', '.'))
                except ValueError:
                    errors.append(_("« %s » doit être un nombre.") % mf.name)
                    continue
                if mf.min_value and num < mf.min_value:
                    errors.append(_("« %s » doit être ≥ %s.") % (mf.name, mf.min_value))
                if mf.max_value and num > mf.max_value:
                    errors.append(_("« %s » doit être ≤ %s.") % (mf.name, mf.max_value))
            measures.append({
                'measure_field_id': mf.id,
                'name': mf.name,
                'unit': mf.unit or '',
                'value_display': raw,
                'sequence': mf.sequence,
            })

        if errors:
            return request.render('website_custom_measure.quote_error', {
                'errors': errors,
                'product': template,
            })

        # --- Détermination du client ---------------------------------------
        if website.is_public_user():
            name = (post.get('contact_name') or '').strip()
            email = (post.get('contact_email') or '').strip()
            phone = (post.get('contact_phone') or '').strip()
            if not name or not email:
                return request.render('website_custom_measure.quote_error', {
                    'errors': [_("Merci d'indiquer votre nom et votre email.")],
                    'product': template,
                })
            Partner = env['res.partner'].sudo()
            partner = Partner.search([('email', '=ilike', email)], limit=1)
            if not partner:
                partner = Partner.create({
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'company_type': 'person',
                })
        else:
            partner = env.user.partner_id

        # --- Description de la ligne (visible sur le devis et le PDF) -------
        description = product.display_name
        for m in measures:
            unit = (' %s' % m['unit']) if m['unit'] else ''
            description += '\n  • %s : %s%s' % (m['name'], m['value_display'], unit)
        note = (post.get('note') or '').strip()
        if note:
            description += '\n  Remarque : %s' % note

        # --- Création du devis ---------------------------------------------
        order = env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'origin': _("Demande de devis sur mesure (site web)"),
            'website_id': website.id,
        })
        line = env['sale.order.line'].sudo().create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'name': description,
        })
        for m in measures:
            env['sale.order.line.measure'].sudo().create({
                'order_line_id': line.id,
                'measure_field_id': m['measure_field_id'],
                'name': m['name'],
                'unit': m['unit'],
                'value_display': m['value_display'],
                'sequence': m['sequence'],
            })

        order.message_post(
            body=_("Demande de devis sur mesure reçue depuis le site web."))

        return request.render('website_custom_measure.quote_thanks', {
            'order': order,
            'partner': partner,
        })
