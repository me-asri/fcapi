from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Response, HTTPException, status, Depends, BackgroundTasks

from jose import jwt
from jose.exceptions import JWTError

from passlib.context import CryptContext
from app.models.result import Result

from app.settings import Settings
from app.tags import Tags
from app.mail import send_mail
from app.dependencies import get_db
from app.models.user import EmailIn, LoginInfo, PassIn, TokenIn, UserUpdate, UserIn, UserDb, UserOut

from app.sql.database import Session
from app.sql.crud import user as crud_user

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Generate random key with `openssl rand -hex 32`
JWT_KEY = '64d016c4f5bee1e80cd3eb8bc42013f997eaac43b56b5aa10a5a1532a17f8655'
JWT_ALGO = 'HS256'
JWT_DEFAULT_EXP_DAYS = 7

router = APIRouter(
    prefix='/users',
    tags=[Tags.users]
)


def get_current_user(fc_authtoken: str = Cookie(default=None), db: Session = Depends(get_db)):
    auth_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Failed to verify token'
    )

    if not fc_authtoken:
        raise auth_exception

    try:
        token_data: dict = jwt.decode(fc_authtoken, JWT_KEY, JWT_ALGO)
        id = token_data.get('sub')
        if not id:
            raise auth_exception
        id = int(id)
    except JWTError:
        raise auth_exception

    user = crud_user.get_user(db, id)
    if not user:
        raise auth_exception

    return user


def get_active_current_user(user: UserDb = Depends(get_current_user)):
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not active',
            headers={'WWW-Authenticate': 'Bearer'}
        )

    return user


def create_access_token(subject: str, exp_delta: Optional[timedelta] = timedelta(days=JWT_DEFAULT_EXP_DAYS)):
    expire = datetime.utcnow() + exp_delta

    token_data = {
        'sub': subject,
        'exp': expire
    }
    token = jwt.encode(token_data, JWT_KEY, JWT_ALGO)

    return token


@router.post(
    '/login',
    response_model=Result
)
def login(info: LoginInfo, response: Response = Response(), db: Session = Depends(get_db)):
    """
    Sets fc_authtoken token cookie based on username and password

    * By default each token lasts up to 7 days
    """

    info.email = info.email.lower()

    user_db = crud_user.get_user_by_email(db, info.email)

    if not user_db or not pwd_context.verify(info.password, user_db.hashed_password):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return Result(code=status.HTTP_401_UNAUTHORIZED, message='Invalid email/password')

    token = create_access_token(str(user_db.id))
    response.set_cookie(key='fc_authtoken', value=token)

    return Result(code=status.HTTP_200_OK, message='Logged in successfully')


@router.get(
    '/login',
    summary='Refresh login token',
    response_model=Result
)
def login(response: Response = Response(), user: UserDb = Depends(get_current_user)):
    """
    Sets fc_authtoken cookie to a newer token that lasts longer than current one
    """

    token = create_access_token(str(user.id))
    response.set_cookie(key='fc_authtoken', value=token)

    return Result(code=status.HTTP_200_OK, message='Token renewed successfully')


@router.post(
    '/',
    summary='Create new user',
    response_model=Result
)
def create_user(user: UserIn, response: Response, tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Creates a new user
    * New users are **inactive** by default
    * A verification email will be sent to specified email to activate created user
    """

    user.email = user.email.lower()

    if crud_user.get_user_by_email(db, user.email):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Result(code=status.HTTP_400_BAD_REQUEST, message='User exists')

    db_user = crud_user.add_user(db, user)

    verify_token = create_access_token(str(db_user.id))
    crud_user.add_user_token(db, verify_token, db_user.id)

    verify_link = f"{Settings.STATIC_URL}/verify.html?token={verify_token}"
    tasks.add_task(
        send_mail,
        user.email,
        'Verify Email Address',
        (f"Hi!\n"
         "We just need to verify your email address before you can use our app.\n"
         f"Verify your email address here:\n"
         f"<a href=\"{verify_link}\">{verify_link}</a>")
    )

    return Result(code=status.HTTP_200_OK, message='User created successfully')


@router.put(
    '/verify',
    summary='Verify user email',
    response_model=Result
)
def verify_user(token: TokenIn, response: Response, db: Session = Depends(get_db)):
    """
    Activates user account after validating email
    """
    invalid_result = Result(
        code=status.HTTP_400_BAD_REQUEST, message='Invalid token')

    try:
        token_data: dict = jwt.decode(token.token, JWT_KEY, JWT_ALGO)
        id = token_data.get('sub')
        if not id:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return invalid_result
        id = int(id)
    except JWTError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return invalid_result

    db_user = crud_user.get_user(db, id)
    if not db_user:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return invalid_result
    if not crud_user.check_user_token(db, token.token, id):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return invalid_result

    # Invalidate unncessary tokens
    if db_user.active:
        crud_user.del_user_token(db, token.token, id)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return invalid_result

    crud_user.activate_user(db, id)
    crud_user.del_user_token(db, token.token, id)

    return Result(code=status.HTTP_200_OK, message='Verified email successfully')


@router.post(
    '/verify',
    summary='Resend verification email',
    response_model=Result
)
def resend_verify(email: EmailIn, response: Response, tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email.email = email.email.lower()

    db_user = crud_user.get_user_by_email(db, email.email)
    if not db_user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return Result(code=status.HTTP_404_NOT_FOUND, message='User does not exist')
    if db_user.active:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Result(code=status.HTTP_400_BAD_REQUEST, message='User already active')

    verify_token = create_access_token(str(db_user.id))
    crud_user.add_user_token(db, verify_token, db_user.id)

    verify_link = f"{Settings.STATIC_URL}/verify.html?token={verify_token}"
    tasks.add_task(
        send_mail,
        db_user.email,
        'Verify Email Address',
        (f"Hi!\n"
         "We just need to verify your email address before you can use our app.\n"
         "Verify your email address here:\n"
         f"<a href=\"{verify_link}\">{verify_link}</a>")
    )

    return Result(code=status.HTTP_200_OK, message='Verification email resent')


@router.get(
    '/me',
    response_model=UserOut,
    summary='Get current user info'
)
def read_user_me(user: UserDb = Depends(get_current_user)):
    """
    Returns information for current user
    """
    return user


@router.delete(
    '/me',
    summary='Delete current user',
    response_model=Result
)
def del_user_me(user: UserDb = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Deletes current user from system
    """

    crud_user.del_user(db, user.id)
    return Result(code=status.HTTP_200_OK, message='User deleted successfully')


@router.put(
    '/me',
    summary='Update current user info',
    response_model=Result
)
def update_user(
    update: UserUpdate,
    response: Response,
    user: UserDb = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates information for current user
    * Current password is necessary only when updating password
    * Returns user information after update
    """

    if update.new_password:
        if not update.current_password or not pwd_context.verify(update.current_password, user.hashed_password):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return Result(code=status.HTTP_401_UNAUTHORIZED, message='Incorrect current password')

    new_user = crud_user.update_user(db, user.id, update)
    if not new_user:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return Result(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message='Failed to update user')

    return Result(code=status.HTTP_200_OK, message='User updated successfully')


@router.post(
    '/password',
    summary='Initiate password reset',
    response_model=Result
)
def pass_reset_init(input: EmailIn, response: Response, tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Initiaites password reset procedure
    1. User will receive an email with link
    2. Clicking on that link will reset user's password
    3. New password will be emailed
    """

    input.email = input.email.lower()

    user_db = crud_user.get_user_by_email(db, input.email)
    if not user_db:
        response.status_code = status.HTTP_404_NOT_FOUND
        return Result(code=status.HTTP_404_NOT_FOUND, message='User does not exist')

    # TODO reuse existing token if possible

    token = create_access_token(str(user_db.id))
    crud_user.add_user_token(db, token, user_db.id)

    reset_link = f"{Settings.STATIC_URL}/reset.html?token={token}"
    tasks.add_task(
        send_mail,
        user_db.email,
        'Reset Account Password',
        (f"Hi\n"
         "We just need to verify your email address before you can reset your password.\n"
         "Reset your password here:\n"
         f"<a href=\"{reset_link}\">{reset_link}</a>")
    )

    return Result(code=status.HTTP_200_OK, message='Password reset initiated')


@router.put(
    '/password/{token}',
    summary='Reset user password',
    response_model=Result
)
def pass_reset(input: PassIn, response: Response, token: str, db=Depends(get_db)):
    """
    Resets user password after verifying token

    *token*: Password reset token emailed to user
    """
    token_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail='Token is not valid'
    )

    bad_token_result = Result(
        code=status.HTTP_400_BAD_REQUEST, message='Invalid auth token')

    try:
        token_data: dict = jwt.decode(token, JWT_KEY, JWT_ALGO)
        id = token_data.get('sub')
        if not id:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return bad_token_result
        id = int(id)
    except JWTError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return bad_token_result

    db_user = crud_user.get_user(db, id)
    if not db_user:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return bad_token_result
    if not crud_user.check_user_token(db, token, id):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return bad_token_result

    crud_user.del_user_token(db, token, id)

    crud_user.update_user(db, id, UserUpdate(new_password=input.password))
    # Activate user as we know they have access to the email
    crud_user.activate_user(db, id)

    return Result(code=status.HTTP_200_OK, message='Password reset successfully')
