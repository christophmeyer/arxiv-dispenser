import React from 'react';
import ErrorIcon from '@mui/icons-material/Error';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import FormControl from 'react-bootstrap/FormControl';
import {FormGroup, FormLabel} from '@material-ui/core';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';

class Header extends React.Component {
  render() {
    return (
      <div>
        <Container>
          <Row>
            <Col>
              <h1>arXiv dispenser</h1>
            </Col>
            <Col style={{textAlign: 'right'}}>
              {this.props.page === 'login' ? null : (
                <LoginIndicator
                  logged_in={this.props.logged_in}
                  username={this.props.username}
                  setLogin={this.props.setLogin}
                  handleLogout={this.props.handleLogout}
                />
              )}
            </Col>
          </Row>
        </Container>
      </div>
    );
  }
}

class LoginIndicator extends React.Component {
  render() {
    if (this.props.logged_in) {
      return (
        <div>
          <Button
            variant='outline-secondary'
            size='sm'
            onClick={() => this.props.handleLogout()}
          >
            {' '}
            Logout{' '}
          </Button>
          <div>Signed in as: {this.props.username}</div>
        </div>
      );
    }
    return (
      <div>
        <CreateUserButton /> <LoginButton setLogin={this.props.setLogin} />
      </div>
    );
  }
}

class LoginButton extends React.Component {
  state = {login_open: false, failed_open: false, username: '', password: ''};

  handleOpenLoginModal = () => this.setState({login_open: true});
  handleCloseLoginModal = () => this.setState({login_open: false});
  handleCloseFailureModal = () => this.setState({failed_open: false});

  handleChangeUsername(value) {
    const value_new = value;
    this.setState(state => ({username: value_new}));
  }

  handleChangePassword(value) {
    const value_new = value;
    this.setState(state => ({password: value_new}));
  }

  handleKeyPress(event) {
    if (event.charCode === 13) {
      this.handleLogin();
    }
  }

  handleLogin = () => {
    fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: this.state.username,
        password: this.state.password,
      }),
    }).then(response => {
      if (response.status !== 200) {
        this.setState({login_open: false, failed_open: true});
      } else if (response.status === 200) {
        this.props.setLogin(this.state.username);
      }
    });
  };

  render() {
    return (
      <>
        <Button
          variant='outline-secondary'
          size='sm'
          onClick={() => this.handleOpenLoginModal()}
        >
          {' '}
          Login{' '}
        </Button>
        <Modal show={this.state.failed_open}>
          <Modal.Body>
            <ErrorIcon fontSize='large' /> Login failed
          </Modal.Body>
          <Modal.Footer>
            <Button variant='secondary' onClick={this.handleCloseFailureModal}>
              Close
            </Button>
          </Modal.Footer>
        </Modal>
        <Modal
          show={this.state.login_open}
          onHide={this.handleCloseLoginModal}
          onKeyPress={e => this.handleKeyPress(e)}
        >
          <Modal.Header>
            <Modal.Title>Login</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <FormGroup className='mb-3'>
              <FormLabel>Username</FormLabel>
              <FormControl
                placeholder='Enter username'
                onChange={e => this.handleChangeUsername(e.target.value)}
              />
            </FormGroup>
            <FormGroup>
              <FormLabel>Password</FormLabel>
              <FormControl
                type='password'
                placeholder='Password'
                onChange={e => this.handleChangePassword(e.target.value)}
              />
            </FormGroup>
          </Modal.Body>
          <Modal.Footer>
            <Button variant='secondary' onClick={this.handleCloseLoginModal}>
              Close
            </Button>
            <Button variant='primary' onClick={this.handleLogin}>
              Login
            </Button>
          </Modal.Footer>
        </Modal>
      </>
    );
  }
}

class CreateUserButton extends React.Component {
  state = {
    create_open: false,
    username: '',
    password: '',
    failed_open: false,
    success_open: false,
  };

  handleOpenCreateModal = () => this.setState({create_open: true});
  handleCloseCreateModal = () => this.setState({create_open: false});
  handleCloseFailureModal = () => this.setState({failed_open: false});
  handleCloseSuccessModal = () => this.setState({success_open: false});

  handleSave = () => {
    this.setState({create_open: false});

    fetch('/api/users', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: this.state.username,
        password: this.state.password,
      }),
    }).then(response => {
      if (response.status !== 200) {
        this.setState({failed_open: true});
      } else if (response.status === 200) {
        this.setState({success_open: true});
      }
    });
  };

  handleKeyPress(event) {
    if (event.charCode === 13) {
      this.handleSave();
    }
  }

  handleChangeUsername(value) {
    const value_new = value;
    this.setState(state => ({username: value_new}));
  }

  handleChangePassword(value) {
    const value_new = value;
    this.setState(state => ({password: value_new}));
  }

  render() {
    return (
      <>
        <Button
          variant='outline-secondary'
          size='sm'
          onClick={() => this.handleOpenCreateModal()}
        >
          {' '}
          Create User{' '}
        </Button>
        <Modal show={this.state.success_open}>
          <Modal.Body>
            <ErrorIcon fontSize='large' /> Successfully created user{' '}
            {this.state.username}.
          </Modal.Body>
          <Modal.Footer>
            <Button variant='secondary' onClick={this.handleCloseSuccessModal}>
              Close
            </Button>
          </Modal.Footer>
        </Modal>
        <Modal show={this.state.failed_open}>
          <Modal.Body>
            <ErrorIcon fontSize='large' /> User creation failed
          </Modal.Body>
          <Modal.Footer>
            <Button variant='secondary' onClick={this.handleCloseFailureModal}>
              Close
            </Button>
          </Modal.Footer>
        </Modal>
        <Modal
          show={this.state.create_open}
          onHide={this.handleClose}
          onKeyPress={e => this.handleKeyPress(e)}
        >
          <Modal.Header>
            <Modal.Title>Create User</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <FormGroup className='mb-3'>
              <FormLabel>Username</FormLabel>
              <FormControl
                type='search'
                value={this.state.username}
                onChange={e => this.handleChangeUsername(e.target.value)}
              ></FormControl>
            </FormGroup>

            <FormGroup>
              <FormLabel>Password</FormLabel>
              <FormControl
                type='password'
                value={this.state.password}
                onChange={e => this.handleChangePassword(e.target.value)}
              ></FormControl>
            </FormGroup>
          </Modal.Body>

          <Modal.Footer>
            <Button variant='secondary' onClick={this.handleCloseCreateModal}>
              Close
            </Button>
            <Button variant='primary' onClick={this.handleSave}>
              Create User
            </Button>
          </Modal.Footer>
        </Modal>
      </>
    );
  }
}

export default Header;
