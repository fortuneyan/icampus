"""
教室预约服务
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, date, time
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.oa.room import OaRoom, OaRoomBooking
from app.models.user import User
from app.core.database import Base


class RoomService:
    """会议室服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        room_type: Optional[str] = None,
        building: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取会议室列表"""
        query = select(OaRoom).where(OaRoom.is_deleted == False)

        if room_type:
            query = query.where(OaRoom.room_type == room_type)
        if building:
            query = query.where(OaRoom.building == building)
        if status:
            query = query.where(OaRoom.status == status)

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        rooms = result.scalars().all()

        items = []
        for room in rooms:
            items.append({
                "id": str(room.id),
                "name": room.name,
                "room_type": room.room_type,
                "building": room.building,
                "floor": room.floor,
                "capacity": room.capacity,
                "equipment": room.equipment,
                "status": room.status,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_by_id(self, room_id: UUID) -> Optional[Dict[str, Any]]:
        """根据ID获取会议室"""
        query = select(OaRoom).where(OaRoom.id == room_id, OaRoom.is_deleted == False)
        result = await self.db.execute(query)
        room = result.scalar_one_or_none()

        if not room:
            return None

        return {
            "id": str(room.id),
            "name": room.name,
            "room_type": room.room_type,
            "building": room.building,
            "floor": room.floor,
            "capacity": room.capacity,
            "equipment": room.equipment,
            "status": room.status,
        }

    async def create(self, data: dict, user_id: UUID) -> Dict[str, Any]:
        """创建会议室"""
        room = OaRoom(
            name=data.get("name"),
            room_type=data.get("room_type", "MEETING_ROOM"),
            building=data.get("building"),
            floor=data.get("floor"),
            capacity=data.get("capacity"),
            equipment=data.get("equipment"),
            status=data.get("status", "ACTIVE"),
        )
        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)
        return {"id": str(room.id), "name": room.name}

    async def update(self, room_id: UUID, data: dict) -> Optional[Dict[str, Any]]:
        """更新会议室"""
        query = select(OaRoom).where(OaRoom.id == room_id, OaRoom.is_deleted == False)
        result = await self.db.execute(query)
        room = result.scalar_one_or_none()

        if not room:
            return None

        for key, value in data.items():
            if hasattr(room, key):
                setattr(room, key, value)

        await self.db.commit()
        await self.db.refresh(room)
        return {"id": str(room.id), "name": room.name}

    async def delete(self, room_id: UUID) -> bool:
        """删除会议室"""
        query = select(OaRoom).where(OaRoom.id == room_id, OaRoom.is_deleted == False)
        result = await self.db.execute(query)
        room = result.scalar_one_or_none()

        if not room:
            return False

        room.is_deleted = True
        await self.db.commit()
        return True

    # API 别名
    async def get_room_list(self, page: int = 1, page_size: int = 20, room_type: Optional[str] = None, building: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """获取教室列表 (API别名)"""
        return await self.get_list(page, page_size, room_type, building, status)

    async def get_room_detail(self, room_id: UUID) -> Optional[Dict[str, Any]]:
        """获取教室详情 (API别名)"""
        return await self.get_by_id(room_id)

    async def create_room(self, data: dict) -> OaRoom:
        """创建教室 (API别名)"""
        room = OaRoom(
            name=data.get("name"),
            room_type=data.get("room_type", "MEETING_ROOM"),
            building=data.get("building"),
            floor=data.get("floor"),
            capacity=data.get("capacity"),
            equipment=data.get("equipment"),
            status=data.get("status", "ACTIVE"),
        )
        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def update_room(self, room_id: UUID, data: dict) -> Optional[OaRoom]:
        """更新教室 (API别名)"""
        query = select(OaRoom).where(OaRoom.id == room_id, OaRoom.is_deleted == False)
        result = await self.db.execute(query)
        room = result.scalar_one_or_none()

        if not room:
            return None

        for key, value in data.items():
            if hasattr(room, key):
                setattr(room, key, value)

        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def delete_room(self, room_id: UUID) -> bool:
        """删除教室 (API别名)"""
        return await self.delete(room_id)

    async def get_room_availability(self, room_id: UUID, query_date: date) -> List[Dict[str, Any]]:
        """获取可用时间段"""
        from app.models.oa.room import OaRoomBooking
        query = select(OaRoomBooking).where(
            OaRoomBooking.room_id == room_id,
            OaRoomBooking.booking_date == query_date,
            OaRoomBooking.status.notin_(["CANCELLED", "REJECTED"]),
        ).order_by(OaRoomBooking.start_time)

        result = await self.db.execute(query)
        bookings = result.scalars().all()

        # 标准时间段
        all_slots = [
            ("08:00", "12:00"),
            ("14:00", "18:00"),
            ("19:00", "21:00"),
        ]

        booked_slots = [(str(b.start_time), str(b.end_time)) for b in bookings]

        available = []
        for start, end in all_slots:
            is_available = True
            for booked_start, booked_end in booked_slots:
                if start < booked_end and end > booked_start:
                    is_available = False
                    break
            available.append({
                "start_time": start,
                "end_time": end,
                "available": is_available,
            })

        return available


class RoomBookingService:
    """会议室预约服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_booking_list(
        self,
        page: int = 1,
        page_size: int = 20,
        room_id: Optional[UUID] = None,
        status: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """获取预约列表"""
        query = select(OaRoomBooking).where(OaRoomBooking.is_deleted == False)

        if room_id:
            query = query.where(OaRoomBooking.room_id == room_id)
        if status:
            query = query.where(OaRoomBooking.status == status)

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页 + 预加载关联
        query = (
            query
            .options(selectinload(OaRoomBooking.room))
            .options(selectinload(OaRoomBooking.applicant))
            .order_by(OaRoomBooking.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        bookings = result.scalars().all()

        items = []
        for booking in bookings:
            items.append({
                "id": str(booking.id),
                "room_id": str(booking.room_id),
                "room_name": booking.room.name if booking.room else None,
                "applicant_id": str(booking.applicant_id),
                "applicant_name": booking.applicant.name if booking.applicant else None,
                "title": booking.title,
                "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
                "start_time": str(booking.start_time) if booking.start_time else None,
                "end_time": str(booking.end_time) if booking.end_time else None,
                "status": booking.status,
                "attendee_count": booking.attendee_count,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_booking_detail(self, booking_id: UUID) -> Optional[Dict[str, Any]]:
        """获取预约详情"""
        query = (
            select(OaRoomBooking)
            .where(OaRoomBooking.id == booking_id, OaRoomBooking.is_deleted == False)
            .options(selectinload(OaRoomBooking.room))
            .options(selectinload(OaRoomBooking.applicant))
        )
        result = await self.db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            return None

        return {
            "id": str(booking.id),
            "room_id": str(booking.room_id),
            "room_name": booking.room.name if booking.room else None,
            "applicant_id": str(booking.applicant_id),
            "applicant_name": booking.applicant.name if booking.applicant else None,
            "title": booking.title,
            "agenda_md": booking.agenda_md,
            "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
            "start_time": str(booking.start_time) if booking.start_time else None,
            "end_time": str(booking.end_time) if booking.end_time else None,
            "status": booking.status,
            "attendee_count": booking.attendee_count,
            "attendees": booking.attendees,
            "reject_reason": booking.reject_reason,
            "created_at": booking.created_at.isoformat() if booking.created_at else None,
        }

    async def create_booking(self, data: dict, user_id: UUID) -> OaRoomBooking:
        """创建预约"""
        booking = OaRoomBooking(
            room_id=data.get("room_id"),
            applicant_id=user_id,
            title=data.get("title"),
            agenda_md=data.get("agenda_md"),
            attendee_count=data.get("attendee_count", 1),
            attendees=data.get("attendees"),
            booking_date=data.get("booking_date"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            status="PENDING",
        )
        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    async def cancel_booking(self, booking_id: UUID, user_id: UUID) -> Optional[OaRoomBooking]:
        """取消预约"""
        query = select(OaRoomBooking).where(
            OaRoomBooking.id == booking_id,
            OaRoomBooking.applicant_id == user_id,
            OaRoomBooking.is_deleted == False,
        )
        result = await self.db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            return None

        booking.status = "CANCELLED"
        booking.cancelled_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    async def remind_approval(self, booking_id: UUID, user_id: UUID) -> bool:
        """催审批"""
        query = select(OaRoomBooking).where(
            OaRoomBooking.id == booking_id,
            OaRoomBooking.applicant_id == user_id,
            OaRoomBooking.status == "PENDING",
        )
        result = await self.db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            return False

        # 标记已发送催办通知
        booking.reminder_sent = True
        await self.db.commit()
        return True

    async def get_my_bookings(
        self,
        user_id: UUID,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取我的预约"""
        query = select(OaRoomBooking).where(
            OaRoomBooking.applicant_id == user_id,
            OaRoomBooking.is_deleted == False,
        )

        if status:
            query = query.where(OaRoomBooking.status == status)

        query = (
            query
            .options(selectinload(OaRoomBooking.room))
            .order_by(OaRoomBooking.created_at.desc())
        )
        result = await self.db.execute(query)
        bookings = result.scalars().all()

        items = []
        for booking in bookings:
            items.append({
                "id": str(booking.id),
                "room_id": str(booking.room_id),
                "room_name": booking.room.name if booking.room else None,
                "title": booking.title,
                "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
                "start_time": str(booking.start_time) if booking.start_time else None,
                "end_time": str(booking.end_time) if booking.end_time else None,
                "status": booking.status,
            })

        return items

    async def get_my_history(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取历史预约"""
        query = select(OaRoomBooking).where(
            OaRoomBooking.applicant_id == user_id,
            OaRoomBooking.is_deleted == False,
            OaRoomBooking.status.in_(["COMPLETED", "CANCELLED"]),
        )

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        query = (
            query
            .options(selectinload(OaRoomBooking.room))
            .order_by(OaRoomBooking.booking_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        bookings = result.scalars().all()

        items = []
        for booking in bookings:
            items.append({
                "id": str(booking.id),
                "room_id": str(booking.room_id),
                "room_name": booking.room.name if booking.room else None,
                "title": booking.title,
                "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
                "start_time": str(booking.start_time) if booking.start_time else None,
                "end_time": str(booking.end_time) if booking.end_time else None,
                "status": booking.status,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def check_conflict(
        self,
        room_id: UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """检查时间冲突"""
        query = select(OaRoomBooking).where(
            OaRoomBooking.room_id == room_id,
            OaRoomBooking.status.notin_(["CANCELLED", "REJECTED"]),
            OaRoomBooking.start_time < end_time,
            OaRoomBooking.end_time > start_time,
        )

        if exclude_id:
            query = query.where(OaRoomBooking.id != exclude_id)

        result = await self.db.execute(query)
        conflicts = result.scalars().all()

        return {
            "has_conflict": len(conflicts) > 0,
            "conflicts": [
                {
                    "id": str(c.id),
                    "title": c.title,
                    "start_time": str(c.start_time),
                    "end_time": str(c.end_time),
                }
                for c in conflicts
            ],
        }

    async def get_available_slots(
        self,
        room_id: UUID,
        target_date: date,
    ) -> List[Dict[str, Any]]:
        """获取可用时间段"""
        # 获取该房间当天已有的预约
        query = select(OaRoomBooking).where(
            OaRoomBooking.room_id == room_id,
            OaRoomBooking.booking_date == target_date,
            OaRoomBooking.status.notin_(["CANCELLED", "REJECTED"]),
        ).order_by(OaRoomBooking.start_time)

        result = await self.db.execute(query)
        bookings = result.scalars().all()

        # 标准时间段: 8:00-12:00, 14:00-18:00, 19:00-21:00
        all_slots = [
            ("08:00", "12:00"),
            ("14:00", "18:00"),
            ("19:00", "21:00"),
        ]

        booked_slots = [
            (str(b.start_time), str(b.end_time)) for b in bookings
        ]

        available = []
        for start, end in all_slots:
            is_available = True
            for booked_start, booked_end in booked_slots:
                # 检查是否重叠
                if start < booked_end and end > booked_start:
                    is_available = False
                    break
            available.append({
                "start_time": start,
                "end_time": end,
                "available": is_available,
            })

        return available
