from rest_framework import serializers
from .models import CustomUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,required=True)
    password2 = serializers.CharField(write_only=True,required=True)
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'age','phone_number','password','password2', 'address', 'relatives_phone_numbers']
    def validate(self, attrs):
         if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Passwords does not matched!!."})
         if len(attrs['password']) < 8:
            raise serializers.ValidationError({"password": "Password must be at least 8 characters long."})
         if CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
         if len(attrs) < 2:
            raise serializers.ValidationError("You can provide atleast 3 relative phone numbers .")
         return attrs
    def create(self, validated_data):
        validated_data.pop('password2') 
        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            age=validated_data.get('age'),
            phone_number=validated_data['phone_number'],
            address=validated_data.get('address', ''),
            relatives_phone_numbers=validated_data.get('relatives_phone_numbers', [])
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
class LoginSerializer(serializers.Serializer):
    email=serializers.EmailField()
    password =serializers.CharField(max_length =100,write_only=True)

    def validate(self, attrs):
        email= attrs.get("email",None)
        password = attrs.get("password",None)

        if email is None : 
            raise serializers.ValidationError("email should required for login")
        if password is None:
            raise serializers.ValidationError("Password should required for login")
        
        return attrs