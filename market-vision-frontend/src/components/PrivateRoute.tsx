import React from 'react';
import { Navigate } from 'react-router-dom';

interface Props {
    children: React.ReactNode;
}

const PrivateRoute: React.FC<Props> = ({ children }) => {
    const token = localStorage.getItem('access_token');
    return token ? <>{children}</> : <Navigate to="/login" replace />;
};

export default PrivateRoute;
