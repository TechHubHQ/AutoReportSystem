from typing import List, Optional
from sqlalchemy import select, update, delete
from app.database.db_connector import get_db
from app.database.models import EmailTemplate


async def create_template(name: str, subject: str, html_content: str, created_by: int):
    """Create a new email template"""
    try:
        db = await get_db()
        new_template = EmailTemplate(
            name=name,
            subject=subject,
            html_content=html_content,
            created_by=created_by
        )
        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        return new_template
    except Exception as e:
        print(f"Error creating template: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()


async def get_templates(user_id: Optional[int] = None) -> List[EmailTemplate]:
    """Get all templates, optionally filtered by user"""
    try:
        db = await get_db()
        query = select(EmailTemplate).where(EmailTemplate.is_active == True)
        if user_id:
            query = query.where(EmailTemplate.created_by == user_id)
        query = query.order_by(EmailTemplate.created_at.desc())
        
        result = await db.execute(query)
        templates = result.scalars().all()
        return templates
    except Exception as e:
        print(f"Error fetching templates: {e}")
        raise e
    finally:
        await db.close()


async def get_template(template_id: int) -> Optional[EmailTemplate]:
    """Get a single template by ID"""
    try:
        db = await get_db()
        result = await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
        template = result.scalar_one_or_none()
        return template
    except Exception as e:
        print(f"Error fetching template: {e}")
        raise e
    finally:
        await db.close()


async def update_template(template_id: int, name: str = None, subject: str = None, html_content: str = None):
    """Update an existing template"""
    try:
        db = await get_db()
        update_data = {}
        if name is not None:
            update_data['name'] = name
        if subject is not None:
            update_data['subject'] = subject
        if html_content is not None:
            update_data['html_content'] = html_content
        
        query = update(EmailTemplate).where(EmailTemplate.id == template_id).values(**update_data)
        await db.execute(query)
        await db.commit()
        return await get_template(template_id)
    except Exception as e:
        print(f"Error updating template: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()


async def delete_template(template_id: int):
    """Soft delete a template"""
    try:
        db = await get_db()
        query = update(EmailTemplate).where(EmailTemplate.id == template_id).values(is_active=False)
        await db.execute(query)
        await db.commit()
        return True
    except Exception as e:
        print(f"Error deleting template: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()