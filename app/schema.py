"""Structural invoice contract; validates types, not factual correctness."""
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator


class InvoiceFields(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    invoice_number: StrictStr | None = Field(alias='发票号码')
    invoice_date: StrictStr | None = Field(alias='开票日期')
    buyer_name: StrictStr | None = Field(alias='购买方名称')
    buyer_tax_id: StrictStr | None = Field(alias='购买方税号')
    total: StrictStr | None = Field(alias='价税合计（小写）')

    @field_validator('*')
    @classmethod
    def reject_blank(cls, value):
        if value is not None and not value.strip():
            raise ValueError('Use null for unreadable fields')
        return value
