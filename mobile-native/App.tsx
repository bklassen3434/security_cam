// mobile-native/App.tsx
import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import EventList from "./src/screens/EventList";
import EventDetail from "./src/screens/EventDetail";

const Stack = createNativeStackNavigator();

const App: React.FC = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: "#101315" },
          headerTintColor: "#fff",
          contentStyle: { backgroundColor: "#101315" },
        }}
      >
        <Stack.Screen
          name="Events"
          component={EventList}
          options={{ title: "Events" }}
        />
        <Stack.Screen
          name="EventDetail"
          component={EventDetail}
          options={{ title: "Event Detail" }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default App;
