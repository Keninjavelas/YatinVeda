import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { apiClient } from '../api/client';

interface ChartData {
  ascendant?: string;
  moon_sign?: string;
  sun_sign?: string;
  nakshatra?: string;
  planets?: Array<{ name: string; sign: string; degree: number; house: number }>;
}

export default function ChartScreen() {
  const [birthDate, setBirthDate] = useState('');
  const [birthTime, setBirthTime] = useState('');
  const [birthPlace, setBirthPlace] = useState('');
  const [chart, setChart] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(false);

  const generateChart = async () => {
    if (!birthDate || !birthTime || !birthPlace) {
      Alert.alert('Required', 'Please fill all fields');
      return;
    }
    setLoading(true);
    try {
      const data = await apiClient.post('/calculations/chart', {
        birth_date: birthDate,
        birth_time: birthTime,
        birth_place: birthPlace,
      });
      setChart(data);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to generate chart');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.header}>Birth Chart</Text>

      <View style={styles.form}>
        <Text style={styles.label}>Birth Date (YYYY-MM-DD)</Text>
        <TextInput
          style={styles.input}
          placeholder="1990-01-15"
          placeholderTextColor="#64748b"
          value={birthDate}
          onChangeText={setBirthDate}
        />
        <Text style={styles.label}>Birth Time (HH:MM)</Text>
        <TextInput
          style={styles.input}
          placeholder="14:30"
          placeholderTextColor="#64748b"
          value={birthTime}
          onChangeText={setBirthTime}
        />
        <Text style={styles.label}>Birth Place</Text>
        <TextInput
          style={styles.input}
          placeholder="Mumbai, India"
          placeholderTextColor="#64748b"
          value={birthPlace}
          onChangeText={setBirthPlace}
        />
        <TouchableOpacity
          style={[styles.button, loading && { opacity: 0.6 }]}
          onPress={generateChart}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Generate Chart</Text>
          )}
        </TouchableOpacity>
      </View>

      {chart && (
        <View style={styles.results}>
          <View style={styles.stat}>
            <Text style={styles.statLabel}>Ascendant</Text>
            <Text style={styles.statValue}>{chart.ascendant || '—'}</Text>
          </View>
          <View style={styles.stat}>
            <Text style={styles.statLabel}>Moon Sign</Text>
            <Text style={styles.statValue}>{chart.moon_sign || '—'}</Text>
          </View>
          <View style={styles.stat}>
            <Text style={styles.statLabel}>Sun Sign</Text>
            <Text style={styles.statValue}>{chart.sun_sign || '—'}</Text>
          </View>
          <View style={styles.stat}>
            <Text style={styles.statLabel}>Nakshatra</Text>
            <Text style={styles.statValue}>{chart.nakshatra || '—'}</Text>
          </View>
          {chart.planets?.map((p) => (
            <View key={p.name} style={styles.planetRow}>
              <Text style={styles.planetName}>{p.name}</Text>
              <Text style={styles.planetInfo}>
                {p.sign} {p.degree.toFixed(1)}° (House {p.house})
              </Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  header: { fontSize: 24, fontWeight: '700', color: '#e2e8f0', marginTop: 48, marginBottom: 16 },
  form: { backgroundColor: '#1e293b', borderRadius: 12, padding: 16, marginBottom: 16 },
  label: { color: '#94a3b8', fontSize: 13, marginBottom: 4, marginTop: 12 },
  input: {
    backgroundColor: '#0f172a',
    borderRadius: 10,
    padding: 14,
    color: '#e2e8f0',
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  button: {
    backgroundColor: '#6366f1',
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    marginTop: 20,
  },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  results: { backgroundColor: '#1e293b', borderRadius: 12, padding: 16 },
  stat: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#334155' },
  statLabel: { color: '#94a3b8', fontSize: 14 },
  statValue: { color: '#818cf8', fontSize: 14, fontWeight: '600' },
  planetRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8 },
  planetName: { color: '#e2e8f0', fontSize: 14, fontWeight: '500' },
  planetInfo: { color: '#94a3b8', fontSize: 13 },
});
