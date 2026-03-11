import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { apiClient } from '../api/client';

interface Profile {
  full_name: string;
  email: string;
  role: string;
  birth_date?: string;
  birth_time?: string;
  birth_place?: string;
  created_at?: string;
}

export default function ProfileScreen({ navigation }: any) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await apiClient.get('/users/me');
        setProfile(data);
      } catch {
        setProfile(null);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleLogout = async () => {
    Alert.alert('Logout', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: async () => {
          await apiClient.logout();
          navigation.replace('Login');
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#818cf8" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.header}>Profile</Text>

      {profile ? (
        <View style={styles.card}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {profile.full_name?.charAt(0)?.toUpperCase() || '?'}
            </Text>
          </View>
          <Text style={styles.name}>{profile.full_name}</Text>
          <Text style={styles.email}>{profile.email}</Text>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{profile.role}</Text>
          </View>

          <View style={styles.details}>
            {profile.birth_date && (
              <View style={styles.row}>
                <Text style={styles.label}>Birth Date</Text>
                <Text style={styles.value}>{profile.birth_date}</Text>
              </View>
            )}
            {profile.birth_time && (
              <View style={styles.row}>
                <Text style={styles.label}>Birth Time</Text>
                <Text style={styles.value}>{profile.birth_time}</Text>
              </View>
            )}
            {profile.birth_place && (
              <View style={styles.row}>
                <Text style={styles.label}>Birth Place</Text>
                <Text style={styles.value}>{profile.birth_place}</Text>
              </View>
            )}
            {profile.created_at && (
              <View style={styles.row}>
                <Text style={styles.label}>Member Since</Text>
                <Text style={styles.value}>
                  {new Date(profile.created_at).toLocaleDateString()}
                </Text>
              </View>
            )}
          </View>
        </View>
      ) : (
        <Text style={styles.error}>Could not load profile</Text>
      )}

      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>Sign Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0f172a' },
  header: { fontSize: 24, fontWeight: '700', color: '#e2e8f0', marginTop: 48, marginBottom: 16 },
  card: { backgroundColor: '#1e293b', borderRadius: 16, padding: 24, alignItems: 'center' },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#6366f1',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatarText: { color: '#fff', fontSize: 28, fontWeight: '700' },
  name: { color: '#e2e8f0', fontSize: 20, fontWeight: '700' },
  email: { color: '#94a3b8', fontSize: 14, marginTop: 2 },
  badge: {
    backgroundColor: '#818cf820',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 8,
    marginTop: 8,
  },
  badgeText: { color: '#818cf8', fontSize: 12, fontWeight: '600', textTransform: 'capitalize' },
  details: { width: '100%', marginTop: 24 },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  label: { color: '#94a3b8', fontSize: 14 },
  value: { color: '#e2e8f0', fontSize: 14, fontWeight: '500' },
  error: { color: '#ef4444', textAlign: 'center', marginTop: 32, fontSize: 16 },
  logoutBtn: {
    backgroundColor: '#ef444420',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 24,
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  logoutText: { color: '#ef4444', fontSize: 16, fontWeight: '600' },
});
