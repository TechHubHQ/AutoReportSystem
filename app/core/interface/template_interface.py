from typing import List, Optional
import os
from sqlalchemy import select, update, delete
from app.database.db_connector import get_db
from app.database.models import EmailTemplate

TEMPLATE_DIR = "app/integrations/email/templates"


class TemplateInterface:
    @staticmethod
    async def create_template(name: str, html_content: str, description: str = "", category: str = "General", user_id: int = None):
        """Create a new template and save to file"""
        try:
            db = await get_db()

            # Generate file path
            filename = f"{name.lower().replace(' ', '_')}.html"
            file_path = os.path.join(TEMPLATE_DIR, filename)

            new_template = EmailTemplate(
                name=name,
                subject=name,  # Use name as subject for now
                description=description,
                category=category,
                html_content=html_content,
                file_path=file_path,
                created_by=user_id or 1
            )
            db.add(new_template)
            await db.commit()
            await db.refresh(new_template)

            # Save to file
            await TemplateInterface._save_template_file(name, html_content)
            return new_template
        except Exception as e:
            print(f"Error creating template: {e}")
            await db.rollback()
            raise e
        finally:
            await db.close()

    @staticmethod
    async def _save_template_file(name: str, html_content: str):
        """Save template content to file"""
        os.makedirs(TEMPLATE_DIR, exist_ok=True)
        filename = f"{name.lower().replace(' ', '_')}.html"
        filepath = os.path.join(TEMPLATE_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

    @staticmethod
    async def sync_templates_from_files():
        """Sync database templates with files in template directory"""
        try:
            db = await get_db()
            template_files = await get_template_files()

            for filename in template_files:
                # Check if template exists in database
                template_name = filename.replace(
                    '.html', '').replace('_', ' ').title()
                result = await db.execute(
                    select(EmailTemplate).where(
                        EmailTemplate.name == template_name)
                )
                existing_template = result.scalar_one_or_none()

                if not existing_template:
                    # Create new template from file
                    file_content = await load_template_from_file(filename)
                    if file_content:
                        new_template = EmailTemplate(
                            name=template_name,
                            subject=template_name,
                            description=f"Template loaded from {filename}",
                            category="File Import",
                            html_content=file_content,
                            file_path=os.path.join(TEMPLATE_DIR, filename),
                            created_by=1  # Default user
                        )
                        db.add(new_template)

            await db.commit()
        except Exception as e:
            print(f"Error syncing templates: {e}")
            await db.rollback()
        finally:
            await db.close()


async def create_template(name: str, subject: str, html_content: str, created_by: int):
    """Legacy function for backward compatibility"""
    return await TemplateInterface.create_template(name, html_content, user_id=created_by)


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


async def get_template_by_name(name: str) -> Optional[EmailTemplate]:
    """Get a single template by name"""
    try:
        db = await get_db()
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.name == name)
        )
        template = result.scalar_one_or_none()
        return template
    except Exception as e:
        print(f"Error fetching template by name: {e}")
        raise e
    finally:
        await db.close()


async def update_template(template_id: int, name: str = None, subject: str = None, html_content: str = None):
    """Update an existing template"""
    try:
        db = await get_db()
        # Get current template for file operations
        current_template = await get_template(template_id)
        old_name = current_template.name if current_template else None

        update_data = {}
        if name is not None:
            update_data['name'] = name
        if subject is not None:
            update_data['subject'] = subject
        if html_content is not None:
            update_data['html_content'] = html_content

        query = update(EmailTemplate).where(
            EmailTemplate.id == template_id).values(**update_data)
        await db.execute(query)
        await db.commit()

        updated_template = await get_template(template_id)

        # Update file if content or name changed
        if html_content is not None or name is not None:
            final_name = name if name is not None else old_name
            final_content = html_content if html_content is not None else current_template.html_content
            await TemplateInterface._save_template_file(final_name, final_content)

            # Remove old file if name changed
            if name is not None and old_name and name != old_name:
                old_filename = f"{old_name.lower().replace(' ', '_')}.html"
                old_filepath = os.path.join(TEMPLATE_DIR, old_filename)
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)

        return updated_template
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
        # Get template name for file deletion
        template = await get_template(template_id)

        query = update(EmailTemplate).where(
            EmailTemplate.id == template_id).values(is_active=False)
        await db.execute(query)
        await db.commit()

        # Remove file
        if template:
            filename = f"{template.name.lower().replace(' ', '_')}.html"
            filepath = os.path.join(TEMPLATE_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)

        return True
    except Exception as e:
        print(f"Error deleting template: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()

# Add new functions for file operations


async def load_template_from_file(filename: str) -> str:
    """Load template content from file"""
    filepath = os.path.join(TEMPLATE_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


async def get_template_files() -> List[str]:
    """Get list of template files"""
    if not os.path.exists(TEMPLATE_DIR):
        return []
    return [f for f in os.listdir(TEMPLATE_DIR) if f.endswith('.html')]
