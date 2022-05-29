import React from 'react';
import Header from './header';
import MainPage from './main';
import 'bootstrap/dist/css/bootstrap.min.css';

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      logged_in: false,
      username: 'default',
    };
  }

  componentDidMount() {
    fetch('/api/logincheck', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(response => response.json())
      .then(data => {
        if (data.logged_in) {
          this.setState(state => ({logged_in: true, username: data.user}));
        }
      });
  }

  setLogin = username => {
    this.setState(state => ({logged_in: true, username: username}));
  };

  setLogout = () => {
    this.setState(state => ({logged_in: false, username: ''}));
  };

  handleLogout = () => {
    fetch('/api/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }).then(response => {
      if (response.status === 200) {
        this.setState(state => ({logged_in: false, username: ''}));
      }
    });
  };

  render() {
    return (
      <div>
        <Header
          logged_in={this.state.logged_in}
          username={this.state.username}
          setLogin={this.setLogin}
          handleLogout={this.handleLogout}
          page={this.state.page}
        />
        <MainPage logged_in={this.state.logged_in} setLogout={this.setLogout} />
      </div>
    );
  }
}

export default App;
