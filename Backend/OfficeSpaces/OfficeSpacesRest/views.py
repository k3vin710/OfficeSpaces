from django.shortcuts import render
from rest_framework.decorators import api_view, authentication_classes, action
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
import json
from django.http import JsonResponse, HttpResponse
from rest_framework import generics, status, viewsets, permissions
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
import datetime
from django.contrib.auth.decorators import login_required
from .models import *
from .models import Attendance
import base64
from django.utils.html import escape
import ast
from django.contrib.auth.models import User
from .permissions import *
from .serializers import *
import pandas as pd
from rest_framework.authtoken.views import APIView
from rest_framework.response import Response
import calendar
import pytz
from datetime import datetime


class SignIn(generics.GenericAPIView):
    def post(self, request):
        username = request.data["Username"]
        password = request.data["Password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            print(token.key)

            login(request, user)
            try:
                p = Profile.objects.get(user_ref=request.user)
                print("1")

                message = {
                    "user_id": p.user_ref.username,
                    "First_Name": p.first_name,
                    "Last_Name": p.last_name,
                    "Address": p.address,
                    "Token": token.key,
                    "Photo": p.photo.url,
                    "Is_Manager": p.Is_Manager,
                    "Flag": 1,
                }
                return JsonResponse(message, status=status.HTTP_200_OK)

            except:

                message = {"Flag": 0, "Message": "There was some error"}
                return JsonResponse(message, status=status.HTTP_400_BAD_REQUEST)

        else:
            message = {"Flag": 0, "Message": "Wrong Credentials enetered"}
            return JsonResponse(message, status=status.HTTP_400_BAD_REQUEST)


class Employee_Data(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [
        Permit,
    ]
    serializer_class = EmployeeSerializer
    queryset = Profile.objects.filter(Is_Manager=False)


class EmployeeInstance(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [TokenAuthentication]
    queryset = Profile.objects.filter()
    serializer_class = EmployeeSerializer


class Add_Violation(generics.GenericAPIView):
    def post(self, request):
        photo = request.data["photo"]
        nv = request.data["nv"]
        sv = Social_distancing_violation(photo_violation=photo, number_of_violations=nv)
        sv.save()
        return JsonResponse("ok", safe=False)


#


class AddAnnouncement(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [Permit]

    def post(self, request, *args, **kwargs):
        try:

            Title = request.data["Title"]
            File = request.data["File"]
            Desc = request.data["Desc"]
            A = Announcements(
                Title=Title, File=File, description=Desc, publisher=request.user
            )
            A.save()
            return JsonResponse("Ok", status=status.HTTP_201_CREATED, safe=False)
        except:
            return JsonResponse("error", status=status.HTTP_400_BAD_REQUEST, safe=False)


#


class AllAnnouncement(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [
        Permit1,
    ]
    serializer_class = AllAnnouncmentSerializer
    queryset = Announcements.objects.all()


class EmployeeAnnoucement(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = {
        Permit1,
    }
    serializer_class = EmployeeSerializer
    emp_announcement = Profile.objects.filter()


class ChartData(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        month = request.data["month"]
        year = request.data["year"]
        if month is not None:
            social_distancing_list = []
            mask_list = []
            sdl = Social_distancing_violation.objects.values(
                "number_of_violations", "date"
            )
            mip = Mask_in_public.objects.values("number_of_violations", "date")
            for i in range(1, calendar.monthrange(int(year), int(month))[1] + 1):
                social_distancing_list.append(0)
                mask_list.append(0)

            month_ = ""
            if len(month) == 1:
                month_ = "0" + month

            if len(month) == 1:
                month_ = "0" + month

            else:
                month_ = month

            for vio in sdl:
                if str(vio["date"])[5:7] == month_:
                    social_distancing_list[int(str(vio["date"])[8:]) - 1] = (
                        social_distancing_list[int(str(vio["date"])[8:]) - 1]
                        + vio["number_of_violations"]
                    )
            for vio in mip:
                if str(vio["date"])[5:7] == month_:
                    mask_list[int(str(vio["date"])[8:]) - 1] = (
                        mask_list[int(str(vio["date"])[8:]) - 1]
                        + vio["number_of_violations"]
                    )
            social_distancing = sum(social_distancing_list)
            mask = sum(mask_list)
        message = {
            "Social_Distancing_Violation_Month": social_distancing,
            "Mask_Violation_Month": mask,
            "Social_Distancing_Violation": social_distancing_list,
            "Mask_Violation": mask_list,
        }
        return JsonResponse(message, status=status.HTTP_200_OK)


class AddAttendance(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        timestamp = str(datetime.datetime.now(pytz.timezone("Asia/Kolkata")))
        date = timestamp[0:10]
        time = timestamp[11:-13]
        time_ = datetime.datetime.strptime(time, "%H:%M:%S").time()
        date_ = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        u = Attendance(user_ref=request.user, date=date_, intime=time_)
        u.save()
        return JsonResponse("OK", status=status.HTTP_200_OK, safe=False)


class GetAttendance(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        attendace = Attendance.objects.filter(user_ref=request.user).values("date")
        attendace_list = []
        for i in attendace:
            attendace_list.append((str(i["date"])))
        message = {
            "Attendance_List": attendace_list,
        }
        return JsonResponse(message, status=status.HTTP_200_OK)

    def post(self, request):
        timestamp = str(datetime.datetime.now(pytz.timezone("Asia/Kolkata")))
        date = timestamp[0:10]
        time = timestamp[11:-13]
        time_ = datetime.datetime.strptime(time, "%H:%M:%S").time()
        date_ = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        u = Attendance(user_ref=request.user, date=date_, intime=time_)
        u.save()
        return JsonResponse("OK", status=status.HTTP_200_OK, safe=False)


class FetchAttendance(generics.GenericAPIView):
    def get(self, request, u_name):
        u = User.objects.get(username=u_name)
        attendace = Attendance.objects.filter(user_ref=u).values("date")
        attendace_list = []
        for i in attendace:
            attendace_list.append((str(i["date"])))
        x = [
            i[6]
            for i in calendar.monthcalendar(datetime.now().year, datetime.now().month)
            if i[6] != 0
        ]
        date = str(datetime.now().date())
        day = int(date[-2:])
        count = 0
        for i in x:
            if i <= day:
                count += 1
        total = 0
        for i in calendar.monthcalendar(datetime.now().year, datetime.now().month):
            for j in i:
                if j != 0 and j <= day:
                    total += 1

        # counting no of days attended and percentage attendance
        attended = 0
        for i in attendace_list:
            if int(i[5:7]) == int(date[5:7]):
                attended += 1
        attendace_percentage = (attended) / (total - count) * 100

        message = {
            "Total_Days": total,
            "Sundays": count,
            "days_attended": attended,
            "Attendance_percentage": attendace_percentage,
        }
        return JsonResponse(message, status=status.HTTP_200_OK)
