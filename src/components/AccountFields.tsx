import { useState } from 'react';
import { StyleSheet, TextInput, View } from 'react-native';

import { colors, radii } from '@/theme';

// Username and password inputs, shared by the welcome screen and "Save your account".
export function AccountFields({
  username,
  password,
  onUsername,
  onPassword,
  onSubmit,
  newPassword,
}: {
  username: string;
  password: string;
  onUsername: (v: string) => void;
  onPassword: (v: string) => void;
  onSubmit: () => void;
  newPassword?: boolean; // creating an account, so iOS offers a strong password
}) {
  const [focused, setFocused] = useState<'username' | 'password' | null>(null);
  return (
    <View style={styles.fields}>
      <TextInput
        value={username}
        onChangeText={onUsername}
        placeholder="Username"
        placeholderTextColor={colors.textMuted}
        autoCapitalize="none"
        autoCorrect={false}
        autoComplete="username"
        textContentType="username"
        returnKeyType="next"
        onFocus={() => setFocused('username')}
        onBlur={() => setFocused(null)}
        style={[styles.input, focused === 'username' && styles.focused]}
      />
      <TextInput
        value={password}
        onChangeText={onPassword}
        placeholder="Password"
        placeholderTextColor={colors.textMuted}
        secureTextEntry
        autoCapitalize="none"
        autoComplete={newPassword ? 'new-password' : 'current-password'}
        textContentType={newPassword ? 'newPassword' : 'password'}
        returnKeyType="go"
        onSubmitEditing={onSubmit}
        onFocus={() => setFocused('password')}
        onBlur={() => setFocused(null)}
        style={[styles.input, focused === 'password' && styles.focused]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  fields: { gap: 10 },
  input: {
    height: 52,
    paddingHorizontal: 16,
    borderRadius: radii.lg,
    borderWidth: 1.5,
    borderColor: colors.hairline,
    backgroundColor: colors.background,
    fontSize: 16,
    color: colors.text,
  },
  focused: { borderColor: colors.primary },
});
