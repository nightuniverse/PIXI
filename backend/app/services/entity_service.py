from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Tuple, Optional
from app.models.entity import Entity, FundingRound, Investment
from app.schemas.entity import EntityCreate, EntityUpdate, EntityFilter
from app.schemas.entity import GrowthScore
from datetime import datetime

class EntityService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_entities(
        self, 
        filters: EntityFilter, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Entity], int]:
        """필터링된 엔티티 목록을 조회합니다."""
        query = self.db.query(Entity)
        
        # 필터 적용
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
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Entity.name.ilike(search_term),
                    Entity.description.ilike(search_term),
                    Entity.domains.overlap([filters.search])
                )
            )
        
        # 총 개수 계산
        total = query.count()
        
        # 페이지네이션 적용
        entities = query.offset(skip).limit(limit).all()
        
        return entities, total
    
    def get_entity(self, entity_id: int) -> Optional[Entity]:
        """특정 엔티티를 조회합니다."""
        return self.db.query(Entity).filter(Entity.id == entity_id).first()
    
    def create_entity(self, entity: EntityCreate) -> Entity:
        """새로운 엔티티를 생성합니다."""
        db_entity = Entity(
            type=entity.type,
            name=entity.name,
            description=entity.description,
            website=str(entity.website) if entity.website else None,
            domains=entity.domains,
            founded_year=entity.founded_year,
            country=entity.country,
            city=entity.city,
            lat=entity.lat,
            lon=entity.lon
        )
        
        self.db.add(db_entity)
        self.db.commit()
        self.db.refresh(db_entity)
        
        return db_entity
    
    def update_entity(self, entity_id: int, entity_update: EntityUpdate) -> Optional[Entity]:
        """엔티티를 업데이트합니다."""
        db_entity = self.get_entity(entity_id)
        if not db_entity:
            return None
        
        update_data = entity_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "website" and value:
                setattr(db_entity, field, str(value))
            else:
                setattr(db_entity, field, value)
        
        db_entity.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_entity)
        
        return db_entity
    
    def delete_entity(self, entity_id: int) -> bool:
        """엔티티를 삭제합니다."""
        db_entity = self.get_entity(entity_id)
        if not db_entity:
            return False
        
        self.db.delete(db_entity)
        self.db.commit()
        
        return True
    
    def calculate_growth_score(self, entity_id: int) -> Optional[GrowthScore]:
        """엔티티의 성장 시그널 점수를 계산합니다."""
        entity = self.get_entity(entity_id)
        if not entity:
            return None
        
        # 성장 시그널 점수 계산 (0-100 스케일)
        factors = {}
        
        # 인력 성장 (35%)
        if entity.headcount_growth_12m_pct is not None:
            hc_score = min(100, max(0, entity.headcount_growth_12m_pct * 10))
            factors["headcount_growth"] = hc_score
        else:
            factors["headcount_growth"] = 0
        
        # 웹 트래픽 트렌드 (25%)
        if entity.web_traffic_trend is not None:
            web_score = min(100, max(0, (entity.web_traffic_trend + 1) * 50))
            factors["web_traffic"] = web_score
        else:
            factors["web_traffic"] = 0
        
        # 깃허브 활동 (15%)
        if entity.github_stars is not None and entity.github_releases_90d is not None:
            gh_score = min(100, max(0, 
                (entity.github_stars / 1000 * 30) + 
                (entity.github_releases_90d * 2)
            ))
            factors["github_activity"] = gh_score
        else:
            factors["github_activity"] = 0
        
        # 채용 강도 (15%)
        if entity.is_hiring and entity.hiring_roles:
            hiring_score = min(100, len(entity.hiring_roles) * 10)
            factors["hiring_intensity"] = hiring_score
        else:
            factors["hiring_intensity"] = 0
        
        # PR 빈도 (10%)
        if entity.pr_frequency is not None:
            pr_score = min(100, entity.pr_frequency * 20)
            factors["pr_frequency"] = pr_score
        else:
            factors["pr_frequency"] = 0
        
        # 최종 점수 계산
        final_score = (
            factors["headcount_growth"] * 0.35 +
            factors["web_traffic"] * 0.25 +
            factors["github_activity"] * 0.15 +
            factors["hiring_intensity"] * 0.15 +
            factors["pr_frequency"] * 0.10
        )
        
        return GrowthScore(
            entity_id=entity_id,
            score=round(final_score, 2),
            factors=factors,
            calculated_at=datetime.utcnow()
        )
