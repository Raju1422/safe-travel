import requests
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import AddressSerializer

class CoordinatesView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddressSerializer(data=request.data)
        
        if serializer.is_valid():
            source_address = serializer.validated_data['source']
            destination_address = serializer.validated_data['destination']

            url = 'https://nominatim.openstreetmap.org/search'

            def get_lat_lng(address):
                params = {
                    'q': address,
                    'format': 'json',
                    'addressdetails': 1
                }
                headers = {
                    'User-Agent': 'YourAppName'
                }
                response = requests.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data:
                            return data[0]['lat'], data[0]['lon']
                    except ValueError:
                        return None, None
                return None, None

            source_lat, source_lng = get_lat_lng(source_address)
            destination_lat, destination_lng = get_lat_lng(destination_address)

            if source_lat is None or destination_lat is None:
                return Response({'error': 'Address not found or invalid address'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'source': {'latitude': source_lat, 'longitude': source_lng},
                'destination': {'latitude': destination_lat, 'longitude': destination_lng}
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
