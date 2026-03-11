import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { apiClient } from '../api/client';

interface Post {
  id: string;
  author_name: string;
  content: string;
  likes: number;
  liked_by_me: boolean;
  created_at: string;
  replies_count: number;
}

export default function CommunityScreen() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [newPost, setNewPost] = useState('');
  const [posting, setPosting] = useState(false);

  const fetchPosts = useCallback(async () => {
    try {
      const data = await apiClient.get('/community/posts');
      setPosts(Array.isArray(data) ? data : data.posts || []);
    } catch {
      setPosts([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchPosts(); }, [fetchPosts]);

  const onRefresh = () => { setRefreshing(true); fetchPosts(); };

  const toggleLike = async (postId: string) => {
    try {
      await apiClient.post(`/community/posts/${postId}/like`);
      setPosts((prev) =>
        prev.map((p) =>
          p.id === postId
            ? { ...p, liked_by_me: !p.liked_by_me, likes: p.liked_by_me ? p.likes - 1 : p.likes + 1 }
            : p,
        ),
      );
    } catch {
      Alert.alert('Error', 'Could not update like');
    }
  };

  const submitPost = async () => {
    const text = newPost.trim();
    if (!text) return;
    setPosting(true);
    try {
      await apiClient.post('/community/posts', { content: text });
      setNewPost('');
      fetchPosts();
    } catch {
      Alert.alert('Error', 'Could not create post');
    } finally {
      setPosting(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#818cf8" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Community</Text>

      <View style={styles.composer}>
        <TextInput
          style={styles.composerInput}
          placeholder="Share something with the community..."
          placeholderTextColor="#64748b"
          value={newPost}
          onChangeText={setNewPost}
          multiline
          maxLength={1000}
        />
        <TouchableOpacity
          style={[styles.postBtn, (!newPost.trim() || posting) && { opacity: 0.4 }]}
          onPress={submitPost}
          disabled={!newPost.trim() || posting}
        >
          {posting ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.postBtnText}>Post</Text>
          )}
        </TouchableOpacity>
      </View>

      <FlatList
        data={posts}
        keyExtractor={(item) => item.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#818cf8" />}
        ListEmptyComponent={<Text style={styles.empty}>No posts yet. Be the first!</Text>}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.author}>{item.author_name}</Text>
              <Text style={styles.time}>{new Date(item.created_at).toLocaleDateString()}</Text>
            </View>
            <Text style={styles.content}>{item.content}</Text>
            <View style={styles.actions}>
              <TouchableOpacity style={styles.actionBtn} onPress={() => toggleLike(item.id)}>
                <Text style={[styles.actionText, item.liked_by_me && styles.liked]}>
                  {item.liked_by_me ? '♥' : '♡'} {item.likes}
                </Text>
              </TouchableOpacity>
              <Text style={styles.actionText}>💬 {item.replies_count}</Text>
            </View>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0f172a' },
  header: { fontSize: 24, fontWeight: '700', color: '#e2e8f0', marginTop: 48, marginBottom: 16 },
  composer: { backgroundColor: '#1e293b', borderRadius: 12, padding: 12, marginBottom: 16 },
  composerInput: {
    color: '#e2e8f0',
    fontSize: 15,
    minHeight: 60,
    textAlignVertical: 'top',
  },
  postBtn: {
    backgroundColor: '#6366f1',
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
    marginTop: 8,
  },
  postBtnText: { color: '#fff', fontWeight: '600' },
  empty: { color: '#64748b', textAlign: 'center', marginTop: 32, fontSize: 16 },
  card: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  author: { color: '#818cf8', fontWeight: '600', fontSize: 14 },
  time: { color: '#64748b', fontSize: 12 },
  content: { color: '#e2e8f0', fontSize: 15, lineHeight: 22, marginBottom: 12 },
  actions: { flexDirection: 'row', gap: 16 },
  actionBtn: { flexDirection: 'row', alignItems: 'center' },
  actionText: { color: '#64748b', fontSize: 14 },
  liked: { color: '#ef4444' },
});
