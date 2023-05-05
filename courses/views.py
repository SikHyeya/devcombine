from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, CSVUploadForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from .models import Course, UserProfile, Tag
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.middleware.csrf import get_token
import csv
from io import TextIOWrapper
from django.urls import reverse
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.forms.models import model_to_dict


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

def get_csrf_token(request):
    token = get_token(request)
    return JsonResponse({'csrf_token': token})

@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return HttpResponseRedirect(reverse('courses:index'))
        else:

            return JsonResponse({'error': 'Invalid request.'}, status=400)
    else:
        form = CustomUserCreationForm()
        return render(request, 'signup.html', {'form': form})

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return HttpResponseRedirect(reverse('courses:index'))
        else:
            return JsonResponse({'error': 'Invalid credentials.'}, status=401)
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@csrf_exempt
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('courses:index'))


def index(request):
    return render(request, 'courses/index.html')


def series(request):
    """
    시리즈명 조회
    """
    return "test"

def series_detail(request, series_id):
    """
    시리즈에 해당하는 코스 조회 (SeriesCourse model)
    """

    return render(request, 'courses/detail.html')

def all_courses(request):

    """
    전체 코스 조회, 필터링 기능
    """
    course_info_list =[]

    all_courses = Course.objects.all()
    for course in all_courses:
        course_info = model_to_dict(course) # 객체 import
        course_info_list.append(course_info)
    context = {
        'all_courses': course_info_list
        }
    # print(context)
    return render(request, 'courses/all_courses.html', context)
    

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_course(request, course_id):
    course = Course.objects.get(id=course_id)
    user_id = request.data.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        course.likes.add(user)
        course.dislikes.remove(user)
        return JsonResponse({}, status=201)
    else:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def dislike_course(request, course_id):
    course = Course.objects.get(id=course_id)
    user_id = request.data.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        course.dislikes.add(user)
        course.likes.remove(user)
        return JsonResponse({}, status=202)
    else:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def check_course_like(request, course_id):
    course = Course.objects.get(id=course_id)
    user_id = request.data.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user in course.likes.all():
            check = 1
        else:
            check = 0
        return JsonResponse({'check': check})
    else:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

#TODO 이유는 모르겠지만 빈 wishlist반환됨.
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def user_wishlist(request):
    user_id = request.data.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        interests = user.userprofile.interests.all()
        wishlist = []
        for interest in interests:
            wishlist.append({
                'id': interest.id,
                'courses': {
                    'course_id': interest.id,
                    'course_name': interest.title,
                }
            })
        return JsonResponse({'wishlist': wishlist}, status=200)
    else:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # CSV 파일을 읽기 모드로 열기
            csv_file = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
            # CSV 파일 파싱하여 Course 모델에 저장
            reader = csv.reader(csv_file)
            next(reader)  # CSV 헤더를 건너뛰기
            now = datetime.now().date()
            for row in reader:
                site = row[0]
                title = row[1]
                instructor = row[2]
                description = row[3]
                url = row[4]
                try:
                    price = Decimal(row[5])
                except InvalidOperation:
                    price = Decimal('0.00')
                tags = row[6]
                rating = row[7]
                try:
                    rating = round(Decimal(row[7]), 3)
                except InvalidOperation:
                    rating = Decimal('0.000')
                thumbnail_url = row[8]
                is_package = bool(row[9])
                is_free = bool(row[10])
                enrollment_count_str = row[11]
                if enrollment_count_str == "" or enrollment_count_str == "0.0":
                    enrollment_count = 0
                else:
                    enrollment_count = int(float(enrollment_count_str))


                upload_date = now

                # Course 모델에 데이터 저장
                course = Course.objects.create(
                    title=title,
                    instructor=instructor,
                    description=description,
                    site=site,
                    url=url,
                    price=price,
                    rating=rating,
                    thumbnail_url=thumbnail_url,
                    is_package=is_package,
                    is_free=is_free,
                    enrollment_count=enrollment_count,
                    upload_date=upload_date,
                )
                for tag_name in tags.split(','):
                    tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
                    course.tags.add(tag)

            return render(request, 'admin/upload_success.html')
    else:
        form = CSVUploadForm()
    return render(request, 'admin/upload.html', {'form': form})

@csrf_exempt
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def course_like_count(request, course_id):
    course = Course.objects.get(id=course_id)
    count = course.likes.count()
    return JsonResponse({'like_count': count})
