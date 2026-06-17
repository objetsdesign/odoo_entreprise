import json

from markupsafe import Markup

from odoo import http, _
from odoo.http import request


class VisualCustomizerController(http.Controller):

    @http.route(
        ['/visual_customizer/quote'],
        type='http', auth='public', website=True,
        methods=['POST'], csrf=True)
    def vc_quote(self, **post):
        env = request.env
        website = request.website

        try:
            tmpl_id = int(post.get('product_template_id'))
        except (TypeError, ValueError):
            return request.redirect('/shop')
        template = env['product.template'].sudo().browse(tmpl_id)
        if not template.exists() or not template.is_visual_customizer:
            return request.redirect('/shop')
        product = template.product_variant_id
        if not product:
            return request.redirect('/shop')

        try:
            qty = float(post.get('quantity') or 1)
        except ValueError:
            qty = 1.0
        if qty <= 0:
            qty = 1.0

        # Composition (texte/images) + couleur produit
        design_json = post.get('design_data') or '[]'
        try:
            layers = json.loads(design_json)
            if not isinstance(layers, list):
                layers = []
        except (ValueError, TypeError):
            layers = []

        color_extra = 0.0
        color_name = (post.get('color_name') or '').strip()
        if post.get('color_id'):
            try:
                color = env['product.vc.color'].sudo().browse(int(post['color_id']))
                if color.exists() and color.product_tmpl_id.id == template.id:
                    color_extra = color.extra_price
                    color_name = color.name
            except (ValueError, TypeError):
                pass

        # Dimensions
        dim_lines = []
        dim_extra = 0.0
        for dim in template.vc_dimension_ids:
            raw = (post.get('dimension_%d' % dim.id) or '').strip()
            if not raw:
                if dim.required:
                    return request.render(
                        'website_visual_customizer.quote_error',
                        {'errors': [_("La dimension « %s » est obligatoire.") % dim.name]})
                continue
            try:
                val = float(raw.replace(',', '.'))
            except ValueError:
                return request.render(
                    'website_visual_customizer.quote_error',
                    {'errors': [_("« %s » doit être un nombre.") % dim.name]})
            if dim.min_value and val < dim.min_value:
                return request.render(
                    'website_visual_customizer.quote_error',
                    {'errors': [_("« %s » doit être ≥ %s.") % (dim.name, dim.min_value)]})
            if dim.max_value and val > dim.max_value:
                return request.render(
                    'website_visual_customizer.quote_error',
                    {'errors': [_("« %s » doit être ≤ %s.") % (dim.name, dim.max_value)]})
            unit = (' %s' % dim.unit) if dim.unit else ''
            dim_lines.append("%s : %s%s" % (dim.name, raw, unit))
            dim_extra += val * (dim.price_per_unit or 0.0)

        # Résumé
        summary_lines = []
        if color_name:
            summary_lines.append(_("Couleur : %s") % color_name)
        for dl in dim_lines:
            summary_lines.append(dl)
        n_text = sum(1 for l in layers if l.get('type') == 'text')
        n_img = sum(1 for l in layers if l.get('type') == 'image')
        for l in layers:
            if l.get('type') == 'text' and l.get('text'):
                summary_lines.append(_("Texte : « %s »") % l.get('text'))
        if n_img:
            summary_lines.append(_("Images / logos : %d") % n_img)
        note = (post.get('note') or '').strip()
        if note:
            summary_lines.append(_("Remarque : %s") % note)
        summary = '\n'.join(summary_lines)

        # Client
        if website.is_public_user():
            name = (post.get('contact_name') or '').strip()
            email = (post.get('contact_email') or '').strip()
            phone = (post.get('contact_phone') or '').strip()
            if not name or not email:
                return request.render(
                    'website_visual_customizer.quote_error',
                    {'errors': [_("Merci d'indiquer votre nom et votre email.")]})
            Partner = env['res.partner'].sudo()
            partner = Partner.search([('email', '=ilike', email)], limit=1)
            if not partner:
                partner = Partner.create({
                    'name': name, 'email': email, 'phone': phone,
                    'company_type': 'person'})
        else:
            partner = env.user.partner_id

        description = product.display_name
        if summary_lines:
            description += '\n' + '\n'.join('  • ' + l for l in summary_lines)

        order = env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'origin': _("Personnalisation visuelle (site web)"),
            'website_id': website.id,
        })
        line = env['sale.order.line'].sudo().create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'name': description,
            'vc_design': design_json,
        })
        line.price_unit = line.price_unit + color_extra + dim_extra

        preview = post.get('preview_image') or ''
        if preview.startswith('data:image') and ',' in preview:
            b64 = preview.split(',', 1)[1]
            try:
                line.vc_preview = b64
                attachment = env['ir.attachment'].sudo().create({
                    'name': 'personnalisation_%s.png' % (order.name or 'devis'),
                    'datas': b64,
                    'res_model': 'sale.order.line',
                    'res_id': line.id,
                    'mimetype': 'image/png',
                })
                body = Markup("<p>%s</p><pre>%s</pre>") % (
                    _("Personnalisation demandée depuis le site web :"), summary)
                order.message_post(body=body, attachment_ids=[attachment.id])
            except Exception:
                order.message_post(body=_("Personnalisation : %s") % summary)
        else:
            order.message_post(body=_("Personnalisation : %s") % summary)

        return request.render('website_visual_customizer.quote_thanks', {
            'order': order,
            'preview': preview if preview.startswith('data:image') else False,
        })
