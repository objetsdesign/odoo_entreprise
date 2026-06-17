# -*- coding: utf-8 -*-
"""Registre des connecteurs.

Chaque connecteur s'enregistre via le décorateur `register`.
Le modèle marketplace.account récupère la classe par son code.
Ce n'est pas un vrai modèle Odoo persistant : il sert uniquement de
point d'accès via self.env (TransientModel léger).
"""
from odoo import models

_CONNECTOR_REGISTRY = {}


def register(code):
    """Décorateur enregistrant une classe de connecteur sous un code."""
    def _wrap(cls):
        _CONNECTOR_REGISTRY[code] = cls
        cls._code = code
        return cls
    return _wrap


class MarketplaceConnectorRegistry(models.AbstractModel):
    _name = 'marketplace.connector.registry'
    _description = 'Registre des connecteurs marketplace'

    def get_connector(self, code):
        return _CONNECTOR_REGISTRY.get(code)

    def available_codes(self):
        return list(_CONNECTOR_REGISTRY.keys())
