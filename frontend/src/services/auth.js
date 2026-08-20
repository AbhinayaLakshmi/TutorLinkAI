import api from "./api";

export const register = async (email, password, fullName, phoneNumber, role) => {
  const response = await api.post("/api/auth/register", {
    email,
    password,
    full_name: fullName,
    phone_number: phoneNumber || null,
    role,
  });
  return response.data;
};

export const login = async (email, password) => {
  const response = await api.post("/api/auth/login", {
    email,
    password,
  });
  const { access_token, user } = response.data;
  localStorage.setItem("token", access_token);
  localStorage.setItem("user", JSON.stringify(user));
  return { access_token, user };
};

export const getCurrentUser = async () => {
  try {
    const response = await api.get("/api/auth/me");
    localStorage.setItem("user", JSON.stringify(response.data));
    return response.data;
  } catch (error) {
    logout();
    throw error;
  }
};

export const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
};

export const isAuthenticated = () => {
  return !!localStorage.getItem("token");
};
