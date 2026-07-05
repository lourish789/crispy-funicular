"""Social community hub: posts, comments, likes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Comment, Post, User
from app.schemas import CommentCreate, PostCreate, PostOut

router = APIRouter(prefix="/api/community", tags=["community"])


@router.get("/posts", response_model=list[PostOut])
def list_posts(topic: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Post)
    if topic:
        q = q.filter(Post.topic == topic)
    return q.order_by(Post.created_at.desc()).limit(100).all()


@router.post("/posts", response_model=PostOut, status_code=201)
def create_post(
    payload: PostCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = Post(
        author_id=current.id,
        author_name=current.full_name,
        author_role=current.role,
        **payload.model_dump(),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("/posts/{post_id}/comments", response_model=PostOut, status_code=201)
def add_comment(
    post_id: int,
    payload: CommentCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comment = Comment(
        post_id=post_id,
        author_id=current.id,
        author_name=current.full_name,
        author_role=current.role,
        body=payload.body,
    )
    db.add(comment)
    db.commit()
    db.refresh(post)
    return post


@router.post("/posts/{post_id}/like", response_model=PostOut)
def like_post(
    post_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.likes += 1
    db.commit()
    db.refresh(post)
    return post
