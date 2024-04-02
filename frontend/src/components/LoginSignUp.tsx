import React, { useState, useEffect } from "react";
import "../App.css";
import { useSpring, animated } from "react-spring";
import { useNavigate } from 'react-router-dom'; // Import useHistory hook from React Router


function LoginSignUp() {
  const [registrationFormStatus, setRegistartionFormStatus] = useState(false);
  const loginProps = useSpring({
    left: registrationFormStatus ? -500 : 0, // Login form sliding positions
  });
  const registerProps = useSpring({
    left: registrationFormStatus ? 0 : 500, // Register form sliding positions
  });

  const loginBtnProps = useSpring({
    borderBottom: registrationFormStatus
      ? "solid 0px transparent"
      : "solid 2px #1059FF", //Animate bottom border of login button
  });
  const registerBtnProps = useSpring({
    borderBottom: registrationFormStatus
      ? "solid 2px #1059FF"
      : "solid 0px transparent", //Animate bottom border of register button
  });

  function registerClicked() {
    setRegistartionFormStatus(true);
  }
  function loginClicked() {
    setRegistartionFormStatus(false);
  }

  return (
    <div className="style">
    <div className="login-register-wrapper">
      <div className="nav-buttons">
        <animated.button
          onClick={loginClicked}
          id="loginBtn"
        //   style={loginBtnProps}
        >
          Login
        </animated.button>
        <animated.button
          onClick={registerClicked}
          id="registerBtn"
        //   style={registerBtnProps}
        >
          Register
        </animated.button>
      </div>
      <div className="form-group">
        <animated.form action="" id="loginform" style={loginProps}>
          <LoginForm />
        </animated.form>
        <animated.form action="" id="registerform" style={registerProps}>
          <RegisterForm />
        </animated.form>
      </div>
      <animated.div className="forgot-panel" style={loginProps}>
        If You Don't have any account Please, Register
      </animated.div>
    </div>
    </div>
  );
}

function LoginForm() {
    const [username, setUsername] = useState("");
    const [password_hash, setPassword] = useState("");
    const navigate = useNavigate();
    const [error, setError] = useState("");

    const handleUsernameChange = (e) => {
        setUsername(e.target.value);
    };

    const handlePasswordChange = (e) => {
        setPassword(e.target.value);
    };

    useEffect(() => {
        if (sessionStorage.getItem("authToken")) {
            navigate("/home");
        }
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Check if any field is empty
        if (!username.trim() || !password_hash.trim()) {
            setError("Please fill in all fields");
            return;
        }

        try {
            const response = await fetch("http://localhost:8100/users/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    username,
                    password_hash,
                }),
            });
            const data = await response.json();
            if (response.ok) {
                // Login successful
                console.log("Login successful:", data.token);
                // If authentication is successful:
                sessionStorage.setItem("authToken", data.token);
                // Redirect user to /home
                navigate('/home');
            } else {
                // Other error handling
                setError(data.detail);
            }
        } catch (error) {
            setError("An error occurred. Please try again later.");
        }
    };

    return (
        <React.Fragment>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            <label htmlFor="usernameInput">USERNAME</label>
            <input
                type="text"
                id="usernameInput"
                value={username}
                onChange={handleUsernameChange}
            />
            <label htmlFor="passwordInput">PASSWORD</label>
            <input
                type="password"
                id="passwordInput"
                value={password_hash}
                onChange={handlePasswordChange}
            />
            <input type="submit" value="submit" className="submit" onClick={handleSubmit} />

        </React.Fragment>
    );
}

  function RegisterForm() {
      const navigate = useNavigate();
      const [error, setError] = useState("");
      const [formData, setFormData] = useState({
          username: "",
          password_hash: "",
          email: "",
          full_name: "",
          address: ""
      });
  
      const handleChange = (e) => {
          const { name, value } = e.target;
          setFormData({
              ...formData,
              [name]: value
          });
      };
  
      const handleSubmit1 = async (e) => {
          e.preventDefault();
          
          // Check if any field is empty
          for (const key in formData) {
              if (!formData[key]) {
                  setError(`Please fill in the ${key.replace('_', ' ')}`);
                  return;
              }
          }
          
          try {
              const response = await fetch('http://localhost:8100/users/register', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/json'
                  },
                  body: JSON.stringify(formData)
              });
              if (response.ok) {
                  alert("Registration successful: Please Login");
                  // Redirect user to login page after successful registration
                  navigate("/login");
              } else {
                  // Other error handling
                  setError("Registration failed");
              }
          } catch (error) {
              console.error('Error registering user:', error.message);
              // Handle error, show an error message to the user
          }
      };
  
      return (
          <React.Fragment>
              {error && <p style={{color:'red'}}>{error}</p>}
              <label htmlFor="username">Username</label>
              <input 
                  type="text" 
                  id="username" 
                  name="username" 
                  value={formData.username} 
                  onChange={handleChange} 
              />
              <label htmlFor="password_hash">Password</label>
              <input 
                  type="password" 
                  id="password_hash" 
                  name="password_hash" 
                  value={formData.password_hash} 
                  onChange={handleChange} 
              />
              <label htmlFor="email">Email</label>
              <input 
                  type="email" 
                  id="email" 
                  name="email" 
                  value={formData.email} 
                  onChange={handleChange} 
              />
              <br/>
              <label htmlFor="full_name">Full Name</label>
              <input 
                  type="text" 
                  id="full_name" 
                  name="full_name" 
                  value={formData.full_name} 
                  onChange={handleChange} 
              />
              <label htmlFor="address">Address</label>
              <input 
                  type="text" 
                  id="address" 
                  name="address" 
                  value={formData.address} 
                  onChange={handleChange} 
              />
              <input type="submit" value="submit" className="submit" onClick={handleSubmit1} />
          </React.Fragment>
      );
  }
  
  


export default LoginSignUp;
