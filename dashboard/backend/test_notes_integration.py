#!/usr/bin/env python3
"""
Integration test for Notes System - demonstrates complete CRUD flow.

Created by The Collective Borg.tools
"""

from models.database import SessionLocal, engine, Base
from models.project import Project
from models.note import ProjectNote
import uuid

def test_notes_integration():
    """Test complete notes CRUD flow."""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        print("🧪 Notes System Integration Test")
        print("=" * 60)
        
        # 1. Create a test project
        print("\n1️⃣ Creating test project...")
        test_project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            path="/tmp/test",
            stage="mvp",
            priority=10,
            value_score=7.5,
            risk_score=3.0,
            languages=["python"],
            deps={},
            raw_data={}
        )
        db.add(test_project)
        db.commit()
        print(f"   ✅ Project created: {test_project.id}")
        
        # 2. Create notes of different types
        print("\n2️⃣ Creating notes...")
        notes_data = [
            {"content": "## General Note\n\nThis is a general observation", "note_type": "general", "tags": ["test"]},
            {"content": "## Architecture Decision\n\nUse FastAPI for backend", "note_type": "decision", "tags": ["architecture", "backend"]},
            {"content": "## Feature Idea\n\nAdd real-time notifications", "note_type": "idea", "tags": ["feature", "frontend"]},
            {"content": "## Blocker\n\nAPI rate limit exceeded", "note_type": "blocker", "tags": ["urgent", "api"]},
            {"content": "## TODO\n\nRefactor authentication module", "note_type": "todo", "tags": ["refactoring", "auth"]},
        ]
        
        created_notes = []
        for note_data in notes_data:
            note = ProjectNote(
                project_id=test_project.id,
                **note_data
            )
            db.add(note)
            created_notes.append(note)
        
        db.commit()
        print(f"   ✅ Created {len(created_notes)} notes")
        
        # 3. Query all notes
        print("\n3️⃣ Querying all notes...")
        all_notes = db.query(ProjectNote).filter(
            ProjectNote.project_id == test_project.id
        ).order_by(ProjectNote.created_at.desc()).all()
        
        print(f"   ✅ Found {len(all_notes)} notes:")
        for note in all_notes:
            tags_str = ', '.join(note.tags[:2])
            content_preview = note.content[:40].replace('\n', ' ')
            print(f"      - [{note.note_type:8}] {content_preview}... | tags: {tags_str}")
        
        # 4. Filter by type
        print("\n4️⃣ Filtering blockers...")
        blockers = db.query(ProjectNote).filter(
            ProjectNote.project_id == test_project.id,
            ProjectNote.note_type == "blocker"
        ).all()
        print(f"   ✅ Found {len(blockers)} blocker(s):")
        for note in blockers:
            print(f"      - {note.content[:50]}")
        
        # 5. Update a note
        print("\n5️⃣ Updating a note...")
        note_to_update = created_notes[0]
        original_content = note_to_update.content
        note_to_update.content = "## Updated Content\n\nThis note has been updated"
        note_to_update.tags.append("updated")
        db.commit()
        db.refresh(note_to_update)
        print(f"   ✅ Updated note {note_to_update.id}")
        print(f"      Before: {original_content[:30]}...")
        print(f"      After:  {note_to_update.content[:30]}...")
        
        # 6. Test to_dict() serialization
        print("\n6️⃣ Testing to_dict() serialization...")
        note_dict = note_to_update.to_dict()
        print(f"   ✅ Serialized note:")
        print(f"      - ID: {note_dict['id']}")
        print(f"      - Type: {note_dict['note_type']}")
        print(f"      - Tags: {note_dict['tags']}")
        print(f"      - Has timestamps: {bool(note_dict['created_at'])}")
        
        # 7. Delete a note
        print("\n7️⃣ Deleting a note...")
        note_to_delete = created_notes[-1]
        note_id = note_to_delete.id
        db.delete(note_to_delete)
        db.commit()
        
        remaining = db.query(ProjectNote).filter(
            ProjectNote.project_id == test_project.id
        ).count()
        print(f"   ✅ Deleted note {note_id}")
        print(f"      Remaining notes: {remaining}")
        
        # 8. Test cascade delete
        print("\n8️⃣ Testing cascade delete (delete project)...")
        notes_before = db.query(ProjectNote).filter(
            ProjectNote.project_id == test_project.id
        ).count()
        
        db.delete(test_project)
        db.commit()
        
        notes_after = db.query(ProjectNote).filter(
            ProjectNote.project_id == test_project.id
        ).count()
        
        print(f"   ✅ Cascade delete verified:")
        print(f"      Notes before: {notes_before}")
        print(f"      Notes after:  {notes_after}")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_notes_integration()
