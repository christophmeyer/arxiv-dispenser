import React from 'react';
import {BookmarkBorder, Bookmark} from '@material-ui/icons';
import Card from 'react-bootstrap/Card';
import MathJax from 'react-mathjax2';
import Badge from 'react-bootstrap/Badge';

class BookmarkToggle extends React.Component {
  addBookmark(paper_id) {
    fetch('/api/users/favorites', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({paper_id: paper_id}),
    }).then(response => {
      if (response.status === 403) {
        this.props.setLogout();
      } else if (response.status === 200) {
        this.props.setFavorite(true);
      }
    });
  }

  removeBookmark(paper_id) {
    fetch('/api/users/favorites', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({paper_id: paper_id}),
    }).then(response => {
      if (response.status === 403) {
        this.props.setLogout();
      } else if (response.status === 200) {
        this.props.setFavorite(false);
      }
    });
  }

  render() {
    if (this.props.logged_in) {
      if (this.props.favorite === true) {
        return (
          <Bookmark onClick={() => this.removeBookmark(this.props.paper_id)} />
        );
      } else if (this.props.favorite === false) {
        return (
          <BookmarkBorder
            onClick={() => this.addBookmark(this.props.paper_id)}
          />
        );
      }
    } else {
      return null;
    }
  }
}

class Paper extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      favorite: this.props.favorite,
    };
  }

  setFavorite = value => {
    const value_new = value;
    this.setState(state => ({favorite: value_new}));
  };

  format_unix_timestamp(unix_timestamp) {
    const timestamp = new Intl.DateTimeFormat('en-GB', {
      weekday: 'long',
      day: 'numeric',
      month: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      timeZoneName: 'short',
    });
    return timestamp.format(new Date(unix_timestamp * 1000));
  }

  render() {
    return (
      <div>
        <br></br>
        <Card border='primary'>
          <Card.Body>
            <Card.Title>
              <Card.Link
                href={'https://arxiv.org/pdf/' + this.props.id}
                target='_blank'
                rel='noreferrer'
                style={{textDecoration: 'none'}}
              >
                {this.props.title}
              </Card.Link>{' '}
              {this.props.affiliations.map(affiliation => (
                <span>
                  <Badge
                    bg='secondary'
                    style={{cursor: 'pointer'}}
                    onClick={() =>
                      this.props.setAffiliationFilter([affiliation])
                    }
                  >
                    {affiliation}
                  </Badge>{' '}
                </span>
              ))}
              <BookmarkToggle
                paper_id={this.props.id}
                favorite={this.state.favorite}
                setFavorite={this.setFavorite}
                setLogout={this.props.setLogout}
                logged_in={this.props.logged_in}
              />
            </Card.Title>
            <Card.Subtitle>
              {this.props.authors.map((author, index) => (
                <span
                  style={{cursor: 'pointer'}}
                  onClick={() =>
                    this.props.setSearchQuery({
                      value: author.name,
                      type: 'author',
                    })
                  }
                >
                  {author.name}
                  {index < this.props.authors.length - 1 ? ', ' : null}
                </span>
              ))}
            </Card.Subtitle>
            {this.format_unix_timestamp(this.props.created)}{' '}
            <Badge bg='light' text='white'>
              <Card.Link
                href={'https://arxiv.org/pdf/' + this.props.id}
                target='_blank'
                rel='noreferrer'
                style={{textDecoration: 'none'}}
              >
                download
              </Card.Link>
            </Badge>
            <br />
            {this.props.arxiv_journal_ref}
            <br />
            <Badge
              pill
              bg='primary'
              style={{cursor: 'pointer'}}
              onClick={() =>
                this.props.setCategoryFilter([this.props.primary_category])
              }
            >
              {this.props.primary_category}
            </Badge>{' '}
            {this.props.categories
              .filter(elem => elem !== this.props.primary_category)
              .map(category => (
                <span>
                  <Badge
                    pill
                    bg='secondary'
                    style={{cursor: 'pointer'}}
                    onClick={() => this.props.setCategoryFilter([category])}
                  >
                    {category}
                  </Badge>{' '}
                </span>
              ))}
            <br></br>
            <Card.Text as='span'>
              <MathJax.Text text={this.props.abstract} />
            </Card.Text>
          </Card.Body>
        </Card>
      </div>
    );
  }
}

export default Paper;
