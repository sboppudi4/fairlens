import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { login as apiLogin, logout as apiLogout, register as apiRegister, fetchMe } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";
import { extractErrorMessage } from "@/api/client";

export function useAuth() {
  const navigate = useNavigate();
  const { user, token, setAuth, clear } = useAuthStore();

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      apiLogin(email, password),
    onSuccess: (resp) => {
      setAuth(resp.access_token, resp.user);
      navigate("/dashboard");
    },
  });

  const registerMutation = useMutation({
    mutationFn: (input: { email: string; password: string; full_name: string }) =>
      apiRegister(input.email, input.password, input.full_name),
    onSuccess: (resp) => {
      setAuth(resp.access_token, resp.user);
      navigate("/dashboard");
    },
  });

  const logoutMutation = useMutation({
    mutationFn: async () => {
      try {
        await apiLogout();
      } catch {
        // even if the server call fails (e.g. expired token), clear locally
      }
    },
    onSettled: () => {
      clear();
      navigate("/login");
    },
  });

  return {
    user,
    isAuthenticated: !!token,
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    logout: logoutMutation.mutate,
    refreshMe: fetchMe,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    loginError: loginMutation.error ? extractErrorMessage(loginMutation.error, "Login failed") : null,
    registerError: registerMutation.error
      ? extractErrorMessage(registerMutation.error, "Registration failed")
      : null,
  };
}
