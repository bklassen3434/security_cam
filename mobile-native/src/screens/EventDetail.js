// src/screens/EventDetail.js
import React from "react";
import { View, Text, Image, StyleSheet, ScrollView } from "react-native";

export default function EventDetail({ route }) {
  const { event } = route.params || {};
  if (!event) {
    return (
      <View style={styles.container}>
        <Text style={styles.error}>No event provided.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 24 }}>
      <Text style={styles.header}>
        {event.label === "UNKNOWN" ? "Unknown face" : "Ben"}
      </Text>
      {event.image_url ? (
        <Image source={{ uri: event.image_url }} style={styles.image} resizeMode="contain" />
      ) : (
        <View style={[styles.image, styles.placeholder]}>
          <Text style={styles.error}>No image</Text>
        </View>
      )}
      <View style={styles.meta}>
        <Text style={styles.row}>Time: {event.timestamp || "n/a"}</Text>
        <Text style={styles.row}>File: {event.filename || "n/a"}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#101315" },
  header: { color: "#fff", fontSize: 20, fontWeight: "700", paddingHorizontal: 16, paddingTop: 12, paddingBottom: 8 },
  image: { width: "100%", height: 360, backgroundColor: "#000" },
  placeholder: { alignItems: "center", justifyContent: "center" },
  meta: { paddingHorizontal: 16, paddingTop: 12 },
  row: { color: "#ddd", fontSize: 14, marginBottom: 6 },
  error: { color: "#f88", padding: 16 },
});
