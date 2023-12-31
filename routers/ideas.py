from .. import models, schemas, utils
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..database import get_db
from sqlalchemy.orm import Session
import os
import shutil
from fastapi import FastAPI, File, UploadFile
from typing import Annotated, List, Optional
from .. import mail
from datetime import datetime
router = APIRouter(
    prefix="/ideas", tags=['ideas']
)


"""@router.get("/")
async def root():
    return {"message": "Hello API"}"""


@router.get("/")
async def get_ideas(db: Session = Depends(get_db), filter: Optional[str] = ""):
    # cursor.execute("""SELECT * FROM ideas """)
    # ideas = cursor.fetchall()
    # print(ideas)

    if filter == "All":
        filter = ""
        ideas = db.query(models.Ideas).order_by(
            models.Ideas.id).filter(models.Ideas.status.contains(filter)).all()
    else:
        ideas = db.query(models.Ideas).order_by(
            models.Ideas.id).filter(models.Ideas.status.contains(filter)).all()
    return ideas


# response_model=schemas.response)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_idea(Idea: schemas.Idea, db: Session = Depends(get_db)):
    # cursor.execute(
    # """ INSERT INTO ideas (shortname,define,objective,businessvalue,contact,status,createdby) VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING * """, (Idea.shortName, Idea.define, Idea.objective, Idea.businessValue, Idea.contacts, Idea.status, Idea.createdby))
    # new_post = cursor.fetchone()
    # conn.commit()
    new_post = models.Ideas(**Idea.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    name = new_post.shortname
    createdby = new_post.createdby
    createdat = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(name, createdat, createdby)
    mail.sendmail(name, createdby, createdat)

    return new_post.id


@router.get("/{id}",)
async def get_idea(id: int, response: Response, db: Session = Depends(get_db)):

    # cursor.execute(f"""SELECT * FROM ideas WHERE id={id} """)
    # idea = cursor.fetchone()
    idea = db.query(models.Ideas).filter(models.Ideas.id == id).first()

    if not idea:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"idea id {id} not found")
        # response.status_code = status.HTTP_404_NOT_FOUND
        # return {"message": f"the {id} is not available in the database"}

    return idea


@router.delete("/{id}")
async def delete_ideas(id: int, response: Response, db: Session = Depends(get_db)):
    # cursor.execute(f"""DELETE FROM ideas WHERE id = {id} RETURNING *""")
    # deleted = cursor.fetchone()
    # conn.commit()

    idea = db.query(models.Ideas).filter(models.Ideas.id == id)
    print(idea.first())
    if idea.first() != None:
        idea.delete(synchronize_session=False)
        db.commit()
        response.status_code = status.HTTP_202_ACCEPTED
        return {"id": id, "title": "deleted", "description": f"Idea ID {id} id deleted from the list"}
    else:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                            detail=f"Idea ID {id} is not available in the DB")


@router.put("/{id}")
async def update_ideas(id: int, response: Response, idea: schemas.Idea, db: Session = Depends(get_db)):
    # cursor.execute("""UPDATE ideas SET shortname = %s, define = %s,objective = %s,businessvalue = %s,contact = %s,status = %s,createdby = %s  WHERE id = %s RETURNING *""",
    # (idea.shortName, idea.define, idea.objective, idea.businessValue, idea.contacts, idea.status, idea.createdby, id))
    # updated = cursor.fetchone()
    # conn.commit()
    update = db.query(models.Ideas).filter(models.Ideas.id == id)
    post = update.first()

    if post != None:
        update.update(idea.model_dump(), synchronize_session=False)
        db.commit()
        return [update.first()]
    else:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Idea ID {id} is not available in the DB")


@router.patch("/status/{id}")
async def update_status(id: int, idea: schemas.UpdateStatus, db: Session = Depends(get_db)):

    data = db.query(models.Ideas).filter(models.Ideas.id == id)

    if data.first() != None:
        data.update(idea.model_dump(), synchronize_session=False)
        db.commit()
        return {"message": "status updated successfully",
                "data": data.first()}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Idea id {id} is not available")
