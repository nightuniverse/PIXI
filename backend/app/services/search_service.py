from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Tuple, Optional
from app.models.entity import Entity
from app.schemas.entity import EntitySearch, EntityList
from datetime import datetime, timedelta

class SearchService:
    def __init__(self, db: Session):
        self.db = db
    
    def search_entities(self, search_query: EntitySearch) -> Tuple[List[Entity], int]:
        """검색 쿼리에 따라 엔티티를 검색합니다."""
        query = self.db.query(Entity)
        
        # 기본 검색어 필터링
        if search_query.query:
            search_term = f"%{search_query.query}%"
            query = query.filter(
                or_(
                    Entity.name.ilike(search_term),
                    Entity.description.ilike(search_term),
                    Entity.domains.overlap([search_query.query])
                )
            )
        
        # 추가 필터 적용
        if search_query.filters:
            filters = search_query.filters
            
            if filters.type:
                query = query.filter(Entity.type == filters.type)
            
            if filters.domains:
                query = query.filter(Entity.domains.overlap(filters.domains))
            
            if filters.country:
                query = query.filter(Entity.country == filters.country)
            
            if filters.city:
                query = query.filter(Entity.city == filters.city)
            
            if filters.funding_stage:
                query = query.filter(Entity.last_funding_round == filters.funding_stage)
            
            if filters.is_hiring is not None:
                query = query.filter(Entity.is_hiring == filters.is_hiring)
            
            if filters.min_funding:
                query = query.filter(Entity.total_funding_usd >= filters.min_funding)
            
            if filters.max_funding:
                query = query.filter(Entity.total_funding_usd <= filters.max_funding)
            
            if filters.min_headcount:
                query = query.filter(Entity.headcount_estimate >= filters.min_headcount)
            
            if filters.max_headcount:
                query = query.filter(Entity.headcount_estimate <= filters.max_headcount)
        
        # 정렬 적용
        if search_query.sort_by == "name":
            if search_query.sort_order == "desc":
                query = query.order_by(desc(Entity.name))
            else:
                query = query.order_by(Entity.name)
        elif search_query.sort_by == "funding":
            if search_query.sort_order == "desc":
                query = query.order_by(desc(Entity.total_funding_usd))
            else:
                query = query.order_by(Entity.total_funding_usd)
        elif search_query.sort_by == "headcount":
            if search_query.sort_order == "desc":
                query = query.order_by(desc(Entity.headcount_estimate))
            else:
                query = query.order_by(Entity.headcount_estimate)
        elif search_query.sort_by == "recent":
            query = query.order_by(desc(Entity.updated_at))
        
        # 총 개수 계산
        total = query.count()
        
        # 페이지네이션 적용
        offset = (search_query.page - 1) * search_query.size
        entities = query.offset(offset).limit(search_query.size).all()
        
        return entities, total
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """검색어 자동완성 제안을 제공합니다."""
        suggestions = []
        
        # 회사명에서 제안
        name_suggestions = self.db.query(Entity.name).filter(
            Entity.name.ilike(f"{query}%")
        ).limit(limit // 2).all()
        
        suggestions.extend([s[0] for s in name_suggestions])
        
        # 도메인에서 제안
        domain_suggestions = self.db.query(Entity.domains).filter(
            Entity.domains.overlap([query])
        ).limit(limit // 2).all()
        
        for domains in domain_suggestions:
            if domains:
                suggestions.extend(domains[:2])  # 각 엔티티에서 최대 2개 도메인
        
        # 중복 제거 및 정렬
        suggestions = list(set(suggestions))[:limit]
        suggestions.sort()
        
        return suggestions
    
    def get_trending_searches(self, limit: int = 10) -> List[dict]:
        """인기 검색어를 제공합니다."""
        # 최근 7일간 업데이트된 엔티티들의 도메인을 기반으로 트렌딩 계산
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        trending_domains = self.db.query(
            func.unnest(Entity.domains).label('domain'),
            func.count(func.unnest(Entity.domains)).label('count')
        ).filter(
            Entity.updated_at >= week_ago
        ).group_by(
            func.unnest(Entity.domains)
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [
            {"domain": domain, "count": count}
            for domain, count in trending_domains
        ]
    
    def get_available_domains(self) -> List[str]:
        """사용 가능한 도메인 태그들을 제공합니다."""
        domains = self.db.query(
            func.unnest(Entity.domains).label('domain')
        ).distinct().all()
        
        return [domain[0] for domain in domains if domain[0]]
    
    def get_available_locations(self) -> dict:
        """사용 가능한 국가/도시들을 제공합니다."""
        # 국가별 도시 목록
        locations = self.db.query(
            Entity.country,
            Entity.city
        ).filter(
            Entity.country.isnot(None),
            Entity.city.isnot(None)
        ).distinct().all()
        
        result = {}
        for country, city in locations:
            if country not in result:
                result[country] = []
            if city not in result[country]:
                result[country].append(city)
        
        # 각 국가의 도시들을 정렬
        for country in result:
            result[country].sort()
        
        return result
