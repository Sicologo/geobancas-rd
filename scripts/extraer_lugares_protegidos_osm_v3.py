#!/usr/bin/env python3
"""Ejecutor rápido para el extractor de lugares protegidos."""
import extraer_lugares_protegidos_osm_v2 as m

m.OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
m.QUERY = m.QUERY.replace("[timeout:180]", "[timeout:75]")

_real_urlopen = m.urllib.request.urlopen

def _urlopen(req, timeout=None, *args, **kwargs):
    return _real_urlopen(req, timeout=min(timeout or 75, 75), *args, **kwargs)

m.urllib.request.urlopen = _urlopen

if __name__ == "__main__":
    raise SystemExit(m.main())
