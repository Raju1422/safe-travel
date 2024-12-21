import json
import requests
import numpy as np
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import websockets
import asyncio
from . models import AddressSerializer
import logging

logger = logging.getLogger(__name__)
# Define the RISK_WEIGHT dictionary

# Define the RISK_WEIGHT dictionary
RISK_WEIGHT = {
    "High Risk": 4,
    "Moderate Risk": 3,
    "Low Risk": 2,
    "Safe": 1,
}

# Function to fetch risk level from WebSocket based on coordinates
async def get_risk_for_coordinates(coordinate):
    try:
        # Send the coordinate in the correct format: a list of dictionaries
        payload = [{'latitude': coordinate['latitude'], 'longitude': coordinate['longitude']}]
        
        async with websockets.connect("ws://localhost:8000/ws/predict-risk/") as websocket:
            # Send the payload as a JSON string
            await websocket.send(json.dumps(payload))
            
            # Receive the response from the WebSocket server
            response = await websocket.recv()
            
            # Parse the JSON response
            risk_data = json.loads(response)
            
            # Get the risk level (assuming it's a list with one entry)
            return risk_data.get('risk_level', ['Safe'])[0]  # Default to 'Safe' if no risk_level is found
    except Exception as e:
        logger.error(f"Error getting risk for coordinate {coordinate}: {e}")
        return 'Safe'  # Default to 'Safe' in case of error


class MultiPathRiskView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            source_address = serializer.validated_data['source']
            destination_address = serializer.validated_data['destination']

            url = 'https://nominatim.openstreetmap.org/search'

            # Fetch latitude and longitude
            def get_lat_lng(address):
                try:
                    params = {'q': address, 'format': 'json', 'addressdetails': 1}
                    headers = {'User-Agent': 'YourAppName'}
                    response = requests.get(url, params=params, headers=headers)
                    response.raise_for_status()  # Raise exception for HTTP errors
                    data = response.json()
                    if data and len(data) > 0:
                        return float(data[0].get('lat', 0)), float(data[0].get('lon', 0))
                except Exception as e:
                    logger.error(f"Error fetching coordinates for {address}: {e}")
                    return None, None

            source_coords = get_lat_lng(source_address)
            destination_coords = get_lat_lng(destination_address)

            if not source_coords or not destination_coords:
                return Response(
                    {'error': 'Invalid source or destination address'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate multiple paths
            def generate_multiple_paths(source, destination, num_paths=5, steps=20):
                paths = []
                for i in range(num_paths):
                    intermediate_path = []
                    for step in range(steps):
                        fraction = min(1, max(0, (step + i * 0.1) / steps))
                        intermediate_lat = source[0] + fraction * (destination[0] - source[0])
                        intermediate_lng = source[1] + fraction * (destination[1] - source[1])
                        intermediate_path.append({"latitude": intermediate_lat, "longitude": intermediate_lng})
                    paths.append(intermediate_path)
                return paths

            paths = generate_multiple_paths(source_coords, destination_coords)

            # Function to classify the paths
            async def classify_paths(paths):
                classified_paths = []
                for path in paths:
                    weighted_sum = 0
                    # For each coordinate in the path, calculate its risk level and compute the weighted sum
                    for coordinate in path:
                        risk_level = await get_risk_for_coordinates(coordinate)
                        weighted_sum += RISK_WEIGHT.get(risk_level, 1)  # Default to 1 if risk is not in the mapping
                    
                    # Calculate the average weighted sum for the path
                    average_weighted_sum = weighted_sum / len(path) if path else 0
                    classified_paths.append({"path": path, "weighted_sum": average_weighted_sum})
                return classified_paths

            # Perform risk classification asynchronously
            try:
                classified_paths = asyncio.run(classify_paths(paths))
            except Exception as e:
                logger.error(f"Error in path classification: {e}")
                return Response(
                    {'error': 'Path classification failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Store the classified paths in the session
            request.session['classified_paths'] = classified_paths

            return Response({'paths': classified_paths})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BestPathDetailsView(APIView):
    def get(self, request, *args, **kwargs):
        session = request.session
        classified_paths = session.get('classified_paths', None)

        if not classified_paths:
            return Response({'error': 'No paths found in session'}, status=status.HTTP_404_NOT_FOUND)

        # Choose the best path based on the minimum weighted sum
        best_path = min(classified_paths, key=lambda x: x['weighted_sum'])

        return Response({'best_path': best_path})







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