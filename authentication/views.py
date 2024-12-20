from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserRegistrationSerializer,LoginSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class UserRegistrationView(APIView):
    def post(self,request):
      try: 
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
      except Exception as e:
          return Response({"error":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      

class LoginView(APIView):
    def post(self,request):
      try: 
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request,username=email,password=password)
            if user is None:
                return Response({"message":"Invalid Email or Password"},status=status.HTTP_404_NOT_FOUND)
            token = get_tokens_for_user(user)
    
            return Response({
                "token":token,
                "username":user.username,
                "email":user.email,
                "id":user.id
                
            },status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
      except Exception as e:
          return Response({"error":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)