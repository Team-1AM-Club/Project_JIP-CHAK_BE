# 완벽: 저장하기 요청 스키마는 property_id/report_id 입력을 UUID 기준으로 반영함.
from uuid import UUID

from pydantic import BaseModel


class CreateBookmarkRequest(BaseModel):
    property_id: UUID
    report_id: UUID | None = None
