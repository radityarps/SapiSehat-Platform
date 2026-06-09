"""DB constraint/index audit for backend foundation."""

from api.db_models import (
    AccountModel,
    AgencyUserModel,
    AuditLogModel,
    CattleProfileModel,
    ClusterRiskSignalModel,
    DetectionEventModel,
    FarmerAccountModel,
    FollowUpModel,
    FusionResultModel,
    RateLimitRequestModel,
    StoredMediaModel,
)


def test_backend_tables_have_expected_constraints_and_indexes():
    assert tuple(AccountModel.__table_args__) == (AccountModel.__table_args__[0],)
    assert AccountModel.__table_args__[0].columns.keys() == ["account_type", "email"]

    assert FarmerAccountModel.__table__.columns.phone_number.unique is True
    assert CattleProfileModel.__table__.columns.farmer_id.index is True
    assert DetectionEventModel.__table__.columns.cattle_id.index is True
    assert StoredMediaModel.__table__.columns.farmer_id.index is True
    assert StoredMediaModel.__table__.columns.detection_id.index is True
    assert FusionResultModel.__table__.columns.disease_class.index is True
    assert FollowUpModel.__table__.columns.status.index is True
    assert ClusterRiskSignalModel.__table__.columns.jurisdiction_id.index is True
    assert RateLimitRequestModel.__table__.columns.client_key.index is True
    assert AuditLogModel.__table__.columns.action.index is True
    assert AgencyUserModel.__table__.columns.role.index is True
