# Layer: Service
"""客户资料 / 密码相关的业务逻辑。

View 层只负责参数校验与响应组装，所有写操作在本层加事务并抛业务异常。
"""

from django.db import transaction

from apps.users.areas import resolve_area_id
from apps.users.exceptions import CaptchaInvalid, OldPasswordIncorrect
from apps.users.models import CustomerProfile
from apps.users.services.captcha_service import CaptchaService


class CustomerProfileService:
    """客户资料：查询（前端字段形态）/ 更新。"""

    @staticmethod
    def _get_or_create(user) -> CustomerProfile:
        profile, _created = CustomerProfile.objects.get_or_create(
            user=user,
            defaults={"contact_phone": user.mobile},
        )
        return profile

    @staticmethod
    def get_profile(user) -> dict:
        """返回前端 userMsg.vue / FullMessage 页直接消费的字段结构。"""
        profile = CustomerProfileService._get_or_create(user)
        return {
            "customerName": profile.company_name,
            "contactName": profile.contact_name,
            "phone": profile.contact_phone,
            "email": profile.email,
            "address": profile.address,
            "licenseUrl": profile.license_url,
            "area": profile.area_path,
            "areaId": profile.area_id,
            "customer_audit_status": profile.audit_status,
            # 前端 FullMessage 页另取的三个别名
            "login_phone": user.mobile,
            "user_email": profile.email,
            "wx_nickname": user.nickname,
        }

    @staticmethod
    @transaction.atomic
    def update_profile(user, data: dict) -> dict:
        """更新当前登录用户的客户资料，重新提交后审核状态回到「审核中」。"""
        profile = CustomerProfileService._get_or_create(user)

        company_name = data.get("customerName") or data.get("company_name")
        contact_name = data.get("contactName") or data.get("contact_name")
        phone = data.get("phone")
        email = data.get("email")
        address = data.get("address")
        license_url = data.get("licenseUrl") or data.get("license_url")
        area_path = data.get("area")
        area_id = data.get("areaId", data.get("area_id"))

        # 传了验证码就必须校验通过（不传则不校验，便于后端 / Swagger 联调）
        captcha = data.get("captcha")
        if captcha:
            target_phone = phone or profile.contact_phone or user.mobile
            if not CaptchaService.verify(target_phone, captcha):
                raise CaptchaInvalid()

        if company_name is not None:
            profile.company_name = company_name
        if contact_name is not None:
            profile.contact_name = contact_name
        if phone is not None:
            profile.contact_phone = phone
        if email is not None:
            profile.email = email
        if address is not None:
            profile.address = address
        if license_url is not None:
            profile.license_url = license_url

        if area_path is not None:
            profile.area_path = area_path
            # 未显式传 areaId 时，用名称路径反查最深层节点 id
            if area_id is None:
                area_id = resolve_area_id(area_path)
        if area_id is not None:
            profile.area_id = area_id

        # 重新提交资料 → 回到审核中
        profile.audit_status = CustomerProfile.AuditStatus.PENDING
        profile.save()
        return CustomerProfileService.get_profile(user)

    @staticmethod
    @transaction.atomic
    def change_password(user, old_password: str, new_password: str) -> None:
        """校验原密码并更新为新密码。"""
        if not user.check_password(old_password):
            raise OldPasswordIncorrect()
        user.set_password(new_password)
        user.save(update_fields=["password"])
