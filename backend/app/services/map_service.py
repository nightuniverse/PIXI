from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Dict, Any, Optional
from app.models.entity import Entity
import math

class MapService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_clusters(self, zoom: float, bounds: Dict[str, float]) -> List[Dict[str, Any]]:
        """지도 줌 레벨과 경계에 따른 클러스터 데이터를 제공합니다."""
        # 줌 레벨에 따른 클러스터 크기 결정
        if zoom < 5:  # 국가 레벨
            cluster_radius = 2.0  # 약 200km
        elif zoom < 10:  # 지역 레벨
            cluster_radius = 0.5  # 약 50km
        elif zoom < 15:  # 도시 레벨
            cluster_radius = 0.1  # 약 10km
        else:  # 상세 레벨
            cluster_radius = 0.01  # 약 1km
        
        # 경계 내 엔티티 조회
        entities = self.db.query(Entity).filter(
            and_(
                Entity.lat >= bounds["south"],
                Entity.lat <= bounds["north"],
                Entity.lon >= bounds["west"],
                Entity.lon <= bounds["east"]
            )
        ).all()
        
        # 간단한 그리드 기반 클러스터링
        clusters = self._create_grid_clusters(entities, cluster_radius)
        
        return clusters
    
    def _create_grid_clusters(self, entities: List[Entity], radius: float) -> List[Dict[str, Any]]:
        """그리드 기반 클러스터링을 수행합니다."""
        clusters = {}
        
        for entity in entities:
            if not entity.lat or not entity.lon:
                continue
            
            # 그리드 좌표 계산
            grid_x = int(entity.lon / radius)
            grid_y = int(entity.lat / radius)
            grid_key = f"{grid_x}_{grid_y}"
            
            if grid_key not in clusters:
                clusters[grid_key] = {
                    "lat": entity.lat,
                    "lon": entity.lon,
                    "count": 0,
                    "entities": [],
                    "center_lat": 0,
                    "center_lon": 0
                }
            
            clusters[grid_key]["count"] += 1
            clusters[grid_key]["entities"].append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "lat": entity.lat,
                "lon": entity.lon
            })
            
            # 클러스터 중심점 업데이트
            clusters[grid_key]["center_lat"] += entity.lat
            clusters[grid_key]["center_lon"] += entity.lon
        
        # 중심점 계산 및 결과 정리
        result = []
        for cluster in clusters.values():
            if cluster["count"] > 0:
                cluster["center_lat"] /= cluster["count"]
                cluster["center_lon"] /= cluster["count"]
                
                result.append({
                    "lat": cluster["center_lat"],
                    "lon": cluster["center_lon"],
                    "count": cluster["count"],
                    "entities": cluster["entities"][:5]  # 최대 5개만 포함
                })
        
        return result
    
    def get_entities_in_bounds(
        self, 
        bounds: Dict[str, float], 
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """특정 경계 내의 엔티티들을 제공합니다."""
        query = self.db.query(Entity).filter(
            and_(
                Entity.lat >= bounds["south"],
                Entity.lat <= bounds["north"],
                Entity.lon >= bounds["west"],
                Entity.lon <= bounds["east"]
            )
        )
        
        if entity_type:
            query = query.filter(Entity.type == entity_type)
        
        entities = query.limit(limit).all()
        
        return [
            {
                "id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "description": entity.description,
                "lat": entity.lat,
                "lon": entity.lon,
                "country": entity.country,
                "city": entity.city,
                "domains": entity.domains,
                "last_funding_round": entity.last_funding_round,
                "is_hiring": entity.is_hiring
            }
            for entity in entities
        ]
    
    def get_heatmap_data(
        self, 
        bounds: Dict[str, float], 
        metric: str = "startup_count"
    ) -> List[Dict[str, Any]]:
        """히트맵 데이터를 제공합니다."""
        # 경계를 그리드로 분할
        grid_size = 0.1  # 약 10km
        grid_data = {}
        
        for lat in range(
            int(bounds["south"] / grid_size),
            int(bounds["north"] / grid_size) + 1
        ):
            for lon in range(
                int(bounds["west"] / grid_size),
                int(bounds["east"] / grid_size) + 1
            ):
                grid_key = f"{lat}_{lon}"
                grid_data[grid_key] = {
                    "lat": lat * grid_size,
                    "lon": lon * grid_size,
                    "value": 0
                }
        
        # 각 그리드에 메트릭 값 집계
        if metric == "startup_count":
            entities = self.db.query(
                func.floor(Entity.lat / grid_size).label('grid_lat'),
                func.floor(Entity.lon / grid_size).label('grid_lon'),
                func.count(Entity.id).label('count')
            ).filter(
                and_(
                    Entity.lat >= bounds["south"],
                    Entity.lat <= bounds["north"],
                    Entity.lon >= bounds["west"],
                    Entity.lon <= bounds["east"]
                )
            ).group_by(
                func.floor(Entity.lat / grid_size),
                func.floor(Entity.lon / grid_size)
            ).all()
            
            for grid_lat, grid_lon, count in entities:
                grid_key = f"{int(grid_lat)}_{int(grid_lon)}"
                if grid_key in grid_data:
                    grid_data[grid_key]["value"] = count
        
        elif metric == "funding_amount":
            entities = self.db.query(
                func.floor(Entity.lat / grid_size).label('grid_lat'),
                func.floor(Entity.lon / grid_size).label('grid_lon'),
                func.coalesce(func.sum(Entity.total_funding_usd), 0).label('total_funding')
            ).filter(
                and_(
                    Entity.lat >= bounds["south"],
                    Entity.lat <= bounds["north"],
                    Entity.lon >= bounds["west"],
                    Entity.lon <= bounds["east"]
                )
            ).group_by(
                func.floor(Entity.lat / grid_size),
                func.floor(Entity.lon / grid_size)
            ).all()
            
            for grid_lat, grid_lon, total_funding in entities:
                grid_key = f"{int(grid_lat)}_{int(grid_lon)}"
                if grid_key in grid_data:
                    grid_data[grid_key]["value"] = total_funding or 0
        
        elif metric == "hiring_count":
            entities = self.db.query(
                func.floor(Entity.lat / grid_size).label('grid_lat'),
                func.floor(Entity.lon / grid_size).label('grid_lon'),
                func.count(Entity.id).label('hiring_count')
            ).filter(
                and_(
                    Entity.lat >= bounds["south"],
                    Entity.lat <= bounds["north"],
                    Entity.lon >= bounds["west"],
                    Entity.lon <= bounds["east"],
                    Entity.is_hiring == True
                )
            ).group_by(
                func.floor(Entity.lat / grid_size),
                func.floor(Entity.lon / grid_size)
            ).all()
            
            for grid_lat, grid_lon, hiring_count in entities:
                grid_key = f"{int(grid_lat)}_{int(grid_lon)}"
                if grid_key in grid_data:
                    grid_data[grid_key]["value"] = hiring_count
        
        # 값이 0보다 큰 그리드만 반환
        return [
            data for data in grid_data.values()
            if data["value"] > 0
        ]
    
    def get_city_statistics(self, city: str, country: str) -> Optional[Dict[str, Any]]:
        """특정 도시의 통계 정보를 제공합니다."""
        entities = self.db.query(Entity).filter(
            and_(
                Entity.city == city,
                Entity.country == country
            )
        ).all()
        
        if not entities:
            return None
        
        # 통계 계산
        total_startups = len([e for e in entities if e.type == "startup"])
        total_investors = len([e for e in entities if e.type == "investor"])
        total_accelerators = len([e for e in entities if e.type == "accelerator"])
        
        total_funding = sum(e.total_funding_usd or 0 for e in entities)
        hiring_companies = len([e for e in entities if e.is_hiring])
        
        # 도메인 분포
        domain_counts = {}
        for entity in entities:
            if entity.domains:
                for domain in entity.domains:
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        top_domains = sorted(
            domain_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            "city": city,
            "country": country,
            "total_entities": len(entities),
            "startups": total_startups,
            "investors": total_investors,
            "accelerators": total_accelerators,
            "total_funding_usd": total_funding,
            "hiring_companies": hiring_companies,
            "top_domains": top_domains
        }
    
    def get_country_statistics(self, country: str) -> Optional[Dict[str, Any]]:
        """특정 국가의 통계 정보를 제공합니다."""
        entities = self.db.query(Entity).filter(
            Entity.country == country
        ).all()
        
        if not entities:
            return None
        
        # 통계 계산
        total_startups = len([e for e in entities if e.type == "startup"])
        total_investors = len([e for e in entities if e.type == "investor"])
        total_accelerators = len([e for e in entities if e.type == "accelerator"])
        
        total_funding = sum(e.total_funding_usd or 0 for e in entities)
        hiring_companies = len([e for e in entities if e.is_hiring])
        
        # 도시별 분포
        city_counts = {}
        for entity in entities:
            if entity.city:
                city_counts[entity.city] = city_counts.get(entity.city, 0) + 1
        
        top_cities = sorted(
            city_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            "country": country,
            "total_entities": len(entities),
            "startups": total_startups,
            "investors": total_investors,
            "accelerators": total_accelerators,
            "total_funding_usd": total_funding,
            "hiring_companies": hiring_companies,
            "top_cities": top_cities
        }
    
    def get_global_overview(self) -> Dict[str, Any]:
        """전 세계 스타트업 생태계 개요를 제공합니다."""
        # 전체 통계
        total_entities = self.db.query(Entity).count()
        total_startups = self.db.query(Entity).filter(Entity.type == "startup").count()
        total_investors = self.db.query(Entity).filter(Entity.type == "investor").count()
        total_accelerators = self.db.query(Entity).filter(Entity.type == "accelerator").count()
        
        # 펀딩 통계
        funding_stats = self.db.query(
            func.count(Entity.id).label('funded_count'),
            func.coalesce(func.sum(Entity.total_funding_usd), 0).label('total_funding')
        ).filter(
            Entity.total_funding_usd > 0
        ).first()
        
        # 채용 통계
        hiring_count = self.db.query(Entity).filter(Entity.is_hiring == True).count()
        
        # 국가별 분포
        country_counts = self.db.query(
            Entity.country,
            func.count(Entity.id).label('count')
        ).filter(
            Entity.country.isnot(None)
        ).group_by(Entity.country).order_by(
            desc('count')
        ).limit(10).all()
        
        return {
            "total_entities": total_entities,
            "startups": total_startups,
            "investors": total_investors,
            "accelerators": total_accelerators,
            "funded_companies": funding_stats.funded_count if funding_stats else 0,
            "total_funding_usd": funding_stats.total_funding if funding_stats else 0,
            "hiring_companies": hiring_count,
            "top_countries": [
                {"country": country, "count": count}
                for country, count in country_counts
            ]
        }
