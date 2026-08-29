# Layer: service
"""楼宇 Mock 服务（/user/getAllLy、/user/getSelectedLy）。"""

from django.db.models import Q

from apps.ads.models import Building


class BuildingService:
    @staticmethod
    def list_buildings(
        selected_only: bool = False,
        search: str = "",
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        """楼宇分页查询。

        - ``selected_only=True``：只返回已选投放楼宇（getSelectedLy）
        - ``search``：按名称/地址模糊匹配（getAllLy 顶部搜索框）
        """
        queryset = Building.objects.filter(is_deleted=False)
        if selected_only:
            queryset = queryset.filter(is_selected=True)
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(address__icontains=search))

        total = queryset.count()
        offset = (page - 1) * page_size
        buildings = queryset[offset : offset + page_size]
        return {
            "total": total,
            "list": [
                {
                    "id": b.id,
                    "name": b.name,
                    "address": b.address,
                    "is_selected": b.is_selected,
                }
                for b in buildings
            ],
        }
