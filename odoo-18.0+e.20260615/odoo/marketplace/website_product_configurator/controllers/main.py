import json

from markupsafe import Markup

from odoo import http, _
from odoo.http import request


class ProductConfiguratorController(http.Controller):

    @http.route(
        ['/product_configurator/quote'],
        type='http', auth='public', website=True,
        methods=['POST'], csrf=True)
    def configurator_quote(self, **post):
        env = request.env
        website = request.website

        # --- Produit -------------------------------------------------------
        try:
            tmpl_id = int(post.get('product_template_id'))
        except (TypeError, ValueError):
            return request.redirect('/shop')
        template = env['product.template'].sudo().browse(tmpl_id)
        if not template.exists() or not template.is_configurable:
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

        # --- Configuration des couleurs (JSON) -----------------------------
        try:
            selection = json.loads(post.get('config_data') or '[]')
            if not isinstance(selection, list):
                selection = []
        except (ValueError, TypeError):
            selection = []

        color_ids = []
        for sel in selection:
            try:
                color_ids.append(int(sel.get('color_id')))
            except (TypeError, ValueError):
                continue
        colors = env['product.config.color'].sudo().browse(color_ids).filtered(
            lambda c: c.product_tmpl_id.id == template.id)
        color_extra = sum(colors.mapped('extra_price'))

        # --- Taille --------------------------------------------------------
        size = None
        if post.get('size_id'):
            try:
                size = env['product.config.size'].sudo().browse(int(post['size_id']))
                if not size.exists() or size.product_tmpl_id.id != template.id:
                    size = None
            except (ValueError, TypeError):
                size = None
        size_extra = size.extra_price if size else 0.0

        # --- Options / propositions ----------------------------------------
        option_lines = []
        option_extra = 0.0
        for opt in template.config_option_ids:
            raw = (post.get('option_%d' % opt.id) or '').strip()
            if opt.option_type == 'boolean':
                checked = bool(raw)
                if checked:
                    option_lines.append("%s : Oui" % opt.name)
                    option_extra += opt.extra_price
                continue
            if not raw:
                if opt.required:
                    return request.render(
                        'website_product_configurator.quote_error', {
                            'errors': [_("L'option « %s » est obligatoire.") % opt.name],
                        })
                continue
            option_lines.append("%s : %s" % (opt.name, raw))
            option_extra += opt.extra_price

        # --- Résumé lisible ------------------------------------------------
        summary_lines = []
        if size:
            summary_lines.append(_("Taille : %s") % size.name)
        for sel in selection:
            part = sel.get('part_name') or ''
            cname = sel.get('color_name') or ''
            if part:
                summary_lines.append("%s : %s" % (part, cname))
        for ol in option_lines:
            summary_lines.append(ol)
        note = (post.get('note') or '').strip()
        if note:
            summary_lines.append(_("Remarque : %s") % note)
        summary = '\n'.join(summary_lines)

        # --- Client --------------------------------------------------------
        if website.is_public_user():
            name = (post.get('contact_name') or '').strip()
            email = (post.get('contact_email') or '').strip()
            phone = (post.get('contact_phone') or '').strip()
            if not name or not email:
                return request.render(
                    'website_product_configurator.quote_error', {
                        'errors': [_("Merci d'indiquer votre nom et votre email.")],
                    })
            Partner = env['res.partner'].sudo()
            partner = Partner.search([('email', '=ilike', email)], limit=1)
            if not partner:
                partner = Partner.create({
                    'name': name, 'email': email, 'phone': phone,
                    'company_type': 'person',
                })
        else:
            partner = env.user.partner_id

        # --- Description de la ligne ---------------------------------------
        description = product.display_name
        if summary:
            description += '\n' + '\n'.join('  • ' + l for l in summary_lines)

        # --- Création du devis ---------------------------------------------
        order = env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'origin': _("Configurateur produit (site web)"),
            'website_id': website.id,
        })
        line = env['sale.order.line'].sudo().create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'name': description,
            'config_summary': summary,
        })

        # Prix = base (pricelist) + suppléments couleur/taille
        line.price_unit = line.price_unit + color_extra + size_extra + option_extra

        # --- Aperçu PNG ----------------------------------------------------
        preview = post.get('preview_image') or ''
        preview_b64 = ''
        if preview.startswith('data:image') and ',' in preview:
            preview_b64 = preview.split(',', 1)[1]
            try:
                line.config_preview = preview_b64
                attachment = env['ir.attachment'].sudo().create({
                    'name': 'apercu_%s.png' % (order.name or 'devis'),
                    'datas': preview_b64,
                    'res_model': 'sale.order.line',
                    'res_id': line.id,
                    'mimetype': 'image/png',
                })
                body = Markup("<p>%s</p><pre>%s</pre>") % (
                    _("Configuration demandée depuis le site web :"), summary)
                order.message_post(body=body, attachment_ids=[attachment.id])
            except Exception:
                order.message_post(body=_("Configuration : %s") % summary)
        else:
            order.message_post(body=_("Configuration : %s") % summary)

        return request.render('website_product_configurator.quote_thanks', {
            'order': order,
            'preview': preview if preview.startswith('data:image') else False,
        })
