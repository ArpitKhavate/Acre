"""Optional cloud integrations: Arize (model monitoring) and Poke (conversational reports).

Both are fed from the same synced data as the web app and degrade gracefully
when their SDK or API key is absent, so the core demo never depends on them.
"""
