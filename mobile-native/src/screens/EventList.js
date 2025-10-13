// src/screens/EventList.js
import React, { useEffect, useState, useCallback } from "react";
import { View, Text, FlatList, Image, StyleSheet, RefreshControl, TouchableOpacity } from "react-native";
import { BACKEND_URL } from "../config";

export default function EventList({ navigation }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${BACKEND_URL}/api/events?limit=100`);
      const json = await res.json();
      setEvents(json.events || []);
    } catch (e) {
      console.log("Fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchEvents(); }, [fetchEvents]);

  const renderItem = ({ item }) => {
    return (
      <TouchableOpacity
        onPress={() => navigation.navigate("EventDetail", { event: item })}
        activeOpacity={0.7}
        style={styles.card}
      >
        {item.image_url ? (
          <Image source={{ uri: item.image_url }} style={styles.image} resizeMode="cover" />
        ) : (
          <View style={[styles.image, styles.imagePlaceholder]}>
            <Text style={styles.placeholderText}>No image</Text>
          </View>
        )}
        <View style={styles.meta}>
          <Text style={styles.title}>{item.label === "UNKNOWN" ? "Unknown face" : "Ben"}</Text>
          <Text style={styles.sub}>{item.timestamp || "n/a"}</Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Event List</Text>
      <FlatList
        data={events}
        keyExtractor={(it, idx) => it.filename ? it.filename : String(idx)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={fetchEvents} />}
        contentContainerStyle={{ paddingBottom: 24 }}
        ListEmptyComponent={<View style={{ padding: 24 }}><Text style={{ color: "#fff" }}>No events yet. Pull to refresh.</Text></View>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#101315" },
  header: { color: "#fff", fontSize: 22, fontWeight: "600", paddingHorizontal: 16, paddingVertical: 12 },
  card: {
    backgroundColor: "#1a1f22",
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#2a2f33",
  },
  image: { width: "100%", height: 200, backgroundColor: "#000" },
  imagePlaceholder: { alignItems: "center", justifyContent: "center" },
  placeholderText: { color: "#999" },
  meta: { padding: 12 },
  title: { color: "#fff", fontSize: 16, fontWeight: "600", marginBottom: 4 },
  sub: { color: "#aaa", fontSize: 13 },
});
