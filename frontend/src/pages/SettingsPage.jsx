import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { useApi } from "../api";
import { addToast } from "../store";
import { Table, Th, Td } from "../components/Table";

export default function SettingsPage() {
  const api = useApi();
  const dispatch = useDispatch();
  const [users, setUsers] = useState([]);

  const loadUsers = async () => {
    try {
      const data = await api.get("/users");
      setUsers(data.users || []);
    } catch {
      dispatch(addToast("Failed to load users", "error"));
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const toggleRole = async (user) => {
    const newRole = user.role === "admin" ? "user" : "admin";
    try {
      await api.put(`/users/${user.id}`, { role: newRole });
      dispatch(addToast("Role updated", "success"));
      loadUsers();
    } catch {
      dispatch(addToast("Failed to update role", "error"));
    }
  };

  return (
    <div className="page-content" style={{ minHeight: "100vh", backgroundColor: "#18181b", color: "white" }}>
      <h2 style={{ fontSize: "1.25rem", marginBottom: "1rem" }}>User Management</h2>
      <Table>
        <thead style={{ backgroundColor: "#27272a" }}>
          <tr>
            <Th>Username</Th>
            <Th>Role</Th>
            <Th>Created</Th>
            <Th>Actions</Th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <Td>{u.username}</Td>
              <Td>{u.role}</Td>
              <Td>{new Date(u.created_at).toLocaleString()}</Td>
              <Td>
                <button
                  onClick={() => toggleRole(u)}
                  style={{ backgroundColor: "#2563eb", color: "white", border: "none", padding: "0.25rem 0.5rem", borderRadius: "0.25rem", cursor: "pointer" }}
                >
                  Make {u.role === "admin" ? "User" : "Admin"}
                </button>
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );
}
