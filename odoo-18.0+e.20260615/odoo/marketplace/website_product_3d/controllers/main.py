import base64
import os

from markupsafe import Markup

from odoo import http, _
from odoo.http import request

# Dossier des modèles .glb fournis avec le module
_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'static', 'src', 'models')


class Product3dController(http.Controller):

    @http.route(
        ['/product_3d/model/<int:tmpl_id>'],
        type='http', auth='public', website=True, methods=['GET'])
    def p3d_model(self, tmpl_id, **kw):
        """Sert le fichier .glb d'un produit.

        Priorité au fichier importé dans le champ binaire ; sinon repli sur
        un modèle fourni avec le module (dossier static/src/models), désigné
        par le nom de fichier p3d_glb_filename.
        """
        template = request.env['product.template'].sudo().browse(tmpl_id)
        if not template.exists() or not template.is_3d:
            return request.not_found()

        data = None
        filename = template.p3d_glb_filename or ('model_%s.glb' % tmpl_id)

        if template.p3d_glb:
            data = base64.b64decode(template.p3d_glb)
        elif template.p3d_glb_filename:
            # Repli : fichier livré avec le module (jamais hors du dossier modèles)
            safe_name = os.path.basename(template.p3d_glb_filename)
            path = os.path.join(_MODELS_DIR, safe_name)
            if os.path.isfile(path):
                with open(path, 'rb') as fh:
                    data = fh.read()

        if data is None:
            return request.not_found()

        headers = [
            ('Content-Type', 'model/gltf-binary'),
            ('Content-Length', str(len(data))),
            ('Content-Disposition', 'inline; filename="%s"' % filename),
            ('Cache-Control', 'public, max-age=86400'),
        ]
        return request.make_response(data, headers=headers)

    @http.route(
        ['/product_3d/quote'],
        type='http', auth='public', website=True,
        methods=['POST'], csrf=True)
    def p3d_quote(self, **post):
        env = request.env
        website = request.website

        try:
            tmpl_id = int(post.get('product_template_id'))
        except (TypeError, ValueError):
            return request.redirect('/shop')
        template = env['product.template'].sudo().browse(tmpl_id)
        if not template.exists() or not template.is_3d:
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

        color_extra = 0.0
        color_name = (post.get('color_name') or '').strip()
        if post.get('color_id'):
            try:
                color = env['product.p3d.color'].sudo().browse(int(post['color_id']))
                if color.exists() and color.product_tmpl_id.id == template.id:
                    color_extra = color.extra_price
                    color_name = color.name
            except (ValueError, TypeError):
                pass

        summary_lines = []
        if color_name:
            summary_lines.append(_("Couleur : %s") % color_name)

        # Image personnalisée uploadée par le client
        custom_image_b64 = (post.get('custom_image_b64') or '').strip()
        has_custom_image = custom_image_b64.startswith('data:image') and ',' in custom_image_b64

        note = (post.get('note') or '').strip()
        if note:
            summary_lines.append(_("Remarque : %s") % note)
        summary = '\n'.join(summary_lines)

        if website.is_public_user():
            name  = (post.get('contact_name')  or '').strip()
            email = (post.get('contact_email') or '').strip()
            phone = (post.get('contact_phone') or '').strip()
            if not name or not email:
                return request.render(
                    'website_product_3d.quote_error',
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
        if has_custom_image:
            description += '\n  • ' + _("Image personnalisée fournie par le client")

        order = env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'origin': _("Configurateur 3D (site web)"),
            'website_id': website.id,
        })
        line = env['sale.order.line'].sudo().create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'name': description,
        })
        line.price_unit = line.price_unit + color_extra

        # Aperçu 3D (capture canvas Three.js)
        preview = post.get('preview_image') or ''
        attachments = []

        if preview.startswith('data:image') and ',' in preview:
            b64_preview = preview.split(',', 1)[1]
            try:
                line.p3d_preview = b64_preview
                att = env['ir.attachment'].sudo().create({
                    'name': 'apercu3d_%s.png' % (order.name or 'devis'),
                    'datas': b64_preview,
                    'res_model': 'sale.order.line',
                    'res_id': line.id,
                    'mimetype': 'image/png',
                })
                attachments.append(att.id)
            except Exception:
                pass

        # Image personnalisée du client (logo / photo)
        if has_custom_image:
            raw_b64 = custom_image_b64.split(',', 1)[1]
            mime    = custom_image_b64.split(';')[0].replace('data:', '')
            ext     = 'png' if 'png' in mime else ('svg' if 'svg' in mime else 'jpg')
            try:
                att_img = env['ir.attachment'].sudo().create({
                    'name': 'image_client_%s.%s' % (order.name or 'devis', ext),
                    'datas': raw_b64,
                    'res_model': 'sale.order.line',
                    'res_id': line.id,
                    'mimetype': mime,
                })
                attachments.append(att_img.id)
            except Exception:
                pass

        body = Markup("<p>%s</p>") % _("Configurateur 3D — demande de devis")
        if summary:
            body += Markup("<pre>%s</pre>") % summary
        if has_custom_image:
            body += Markup("<p><em>%s</em></p>") % _("Image personnalisée jointe.")
        order.message_post(body=body, attachment_ids=attachments)

        return request.render('website_product_3d.quote_thanks', {
            'order': order,
            'preview': preview if preview.startswith('data:image') else False,
        })
