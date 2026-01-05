"""
./backend/utils/geo.py

Helper function with geolocation calculations and measurements using Haversine formula.
"""
from typing import Any
import math

class Haversine:
    def __init__(
            self,
            lat1:float,
            lon1:float,
            lat2:float,
            lon2:float
    ) -> None:
        self.lat1 = lat1
        self.lon1 = lon1
        self.lat2 = lat2
        self.lon2 = lon2

    def convert_to_radians(self) -> tuple:
        """
        Converts a set of four coordinates (2 start, 2 end) to radians.

        Returns:
            tuple: Contains all coordinates converted to radians and the differences between them.
        """

        coords_deg = [[self.lat1, self.lon1], [self.lat2, self.lon2]]
        coords_rad = []

        for coord_set in coords_deg:
            temp = []
            for coord in coord_set:
                coord_rad = coord * math.pi/180
                temp.append(coord_rad)
            coords_rad.append(temp)

        lat1_rad = coords_rad[0][0]
        lon1_rad = coords_rad[0][1]
        lat2_rad = coords_rad[1][0]
        lon2_rad = coords_rad[1][1]

        delta_lat = lat2_rad - lat1_rad
        delta_lon = lon2_rad - lon1_rad

        return lat1_rad, lon1_rad, lat2_rad, lon2_rad, delta_lat, delta_lon

    def haversine_of_central_ang(self) -> float:
        """
        Using geometric functions to calculate the haversine of the central angle, otherwise known
        as "a". This is the half of the versed sine of an angle. (versed sine = 1 - cos).

        Returns:
            float: Returns the haversine of the central angle formed between the two coordinates.
        """
        results = self.convert_to_radians()
        lat1_rad = results[0]
        lat2_rad = results[2]

        delta_lat = results[4]
        delta_lon = results[5]

        a = (math.sin(delta_lat / 2)) ** 2
        a += math.cos(lat1_rad) * math.cos(lat2_rad) * (math.sin(delta_lon / 2)) ** 2
        return a

    def angular_distance(self) -> float:
        """
        Calculation of the angular distance, "c" using the haversine of the central angle, "a".

        Returns:
            float: Angular distance between the two points.
        """
        a = self.haversine_of_central_ang()
        c = 2 * math.asin(math.sqrt(a))
        return c

    def final_distance(self) -> float:
        """
        Calculates the final distance between the two points. "r" is the Earth's radius in km.

        Returns:
            float: Final distance in km
        """
        c = self.angular_distance()
        r = 6371
        d = r * c
        return d
