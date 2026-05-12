from sqlalchemy import func
from geoalchemy2 import Geography


def point_expr(lat: float, lng: float):
    return func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)


def distance_m_expr(geom, lat: float, lng: float):
    point = point_expr(lat, lng)
    return func.ST_Distance(
        func.cast(geom, Geography),
        func.cast(point, Geography),
    )


def within_radius_expr(geom, lat: float, lng: float, radius_m: int):
    point = point_expr(lat, lng)
    return func.ST_DWithin(
        func.cast(geom, Geography),
        func.cast(point, Geography),
        radius_m,
    )
