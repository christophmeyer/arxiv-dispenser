import React from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Accordion from 'react-bootstrap/Accordion';
import Spinner from 'react-bootstrap/Spinner';
import DeleteIcon from '@mui/icons-material/Delete';
import Filters from './filters';
import InputGroup from 'react-bootstrap/InputGroup';
import FormControl from 'react-bootstrap/FormControl';
import SearchIcon from '@material-ui/icons/Search';
import Select from 'react-select';
import Paper from './paper';
import MathJax from 'react-mathjax2';

class MainPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      query: {value: '', type: 'full_text'},
      filters: {time: 'last_day', affiliations: [], categories: []},
      logged_in: this.props.logged_in,
      available_categories: [],
      available_affiliations: [],
      selected_tab: 'all',
      expand_all: false,
    };
  }

  flipExpandAll = value => {
    this.setState(state => ({expand_all: !this.state.expand_all}));
  };

  setExpandAll = value => {
    this.setState(state => ({expand_all: value}));
  };

  handleSaveClick(description) {
    fetch('/api/saved', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        description: description,
        time: this.state.filters.time,
        search_string: this.state.query.value,
        search_type: this.state.query.type,
        categories: this.state.filters.categories,
        affiliations: this.state.filters.affiliations,
      }),
    });
  }

  componentDidMount() {
    fetch('/api/categories', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(response => response.json())
      .then(data => {
        this.setState(state => ({available_categories: data.categories}));
      });

    fetch('/api/organizations', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(response => response.json())
      .then(data => {
        this.setState(state => ({
          available_affiliations: data.organizations,
        }));
      });
  }

  componentDidUpdate(prevProps) {
    if (this.props.logged_in !== prevProps.logged_in) {
      this.setState(state => ({
        selected_tab: 'all',
        filter: {time: 'last_day', affiliations: [], categories: []},
      }));
    }
  }

  setTimeFilter(value) {
    const value_new = {...this.state.filters, time: value};
    this.setState(state => ({filters: value_new}));
  }

  setCategoryFilter(value) {
    const value_new = {...this.state.filters, categories: value};
    this.setState(state => ({filters: value_new}));
  }

  setAffiliationFilter(value) {
    const value_new = {...this.state.filters, affiliations: value};
    this.setState(state => ({filters: value_new}));
  }

  setSearchQuery(value) {
    const value_new = value;
    this.setState(state => ({query: value_new}));
  }

  setSelectedTab(value) {
    const value_new = value;
    this.setState(state => ({selected_tab: value_new}));
  }

  render() {
    if (this.state.selected_tab === 'custom') {
      return (
        <div>
          <Container>
            <Row className='justify-content-md-center'>
              <br />
              <Col xs={8}>
                <SearchBar
                  setSearchQuery={value => this.setSearchQuery(value)}
                  query={this.state.query}
                />
              </Col>
            </Row>
            <Filters
              logged_in={this.props.logged_in}
              handleSaveClick={description => this.handleSaveClick(description)}
              filters={this.state.filters}
              available_affiliations={this.state.available_affiliations}
              available_categories={this.state.available_categories}
              setTimeFilter={value => this.setTimeFilter(value)}
              setAffiliationFilter={value => this.setAffiliationFilter(value)}
              setCategoryFilter={value => this.setCategoryFilter(value)}
              setSelectedTab={value => this.setSelectedTab(value)}
              selected_tab={this.state.selected_tab}
              expand_all={this.state.expand_all}
              flipExpandAll={value => this.flipExpandAll(value)}
            />
            <Row>
              <MultiScrollField
                setExpandAll={value => this.setExpandAll(value)}
                setLogout={this.props.setLogout}
                logged_in={this.props.logged_in}
                expand_all={this.state.expand_all}
              />
            </Row>
          </Container>
        </div>
      );
    } else {
      return (
        <div>
          <Container>
            <Row className='justify-content-md-center'>
              <br />
              <Col xs={8}>
                <SearchBar
                  setSearchQuery={value => this.setSearchQuery(value)}
                  query={this.state.query}
                />
              </Col>
            </Row>
            <Filters
              logged_in={this.props.logged_in}
              filters={this.state.filters}
              handleSaveClick={description => this.handleSaveClick(description)}
              available_affiliations={this.state.available_affiliations}
              available_categories={this.state.available_categories}
              setTimeFilter={value => this.setTimeFilter(value)}
              setAffiliationFilter={value => this.setAffiliationFilter(value)}
              setCategoryFilter={value => this.setCategoryFilter(value)}
              setSelectedTab={value => this.setSelectedTab(value)}
              selected_tab={this.state.selected_tab}
            />
            <Row>
              <ScrollField
                filters={this.state.filters}
                query={this.state.query}
                selected_tab={this.state.selected_tab}
                setLogout={this.props.setLogout}
                logged_in={this.props.logged_in}
                setSearchQuery={value => this.setSearchQuery(value)}
                setCategoryFilter={value => this.setCategoryFilter(value)}
                setAffiliationFilter={value => this.setAffiliationFilter(value)}
              />
            </Row>
          </Container>
        </div>
      );
    }
  }
}

class MultiScrollField extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      saved_filter_collections: [],
      logged_in: this.props.logged_in,
      active_keys: this.props.expand_all
        ? Array.from({length: this.state.queries.length}, (v, k) => k)
        : [],
    };
  }

  componentDidUpdate(prevProps) {
    if (this.props.expand_all !== prevProps.expand_all) {
      this.setState(state => ({
        active_keys: this.props.expand_all
          ? Array.from(
              {length: this.state.saved_filter_collections.length},
              (v, k) => k
            )
          : [],
      }));
    }
  }

  componentDidMount() {
    fetch('/api/saved', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(response => response.json())
      .then(data => {
        this.setState(state => ({
          saved_filter_collections: data.saved_queries,
        }));
      });
  }

  handleDeleteClick(event_key, query_id) {
    fetch('/api/saved', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({query_id: query_id}),
    }).then(response => {
      if (response.status === 403) {
        this.props.setLogout();
      } else if (response.status === 200) {
        var updated_active_keys = this.state.active_keys
          .filter(num => num != event_key)
          .map(num => (num > event_key ? num - 1 : num));
        this.setState(state => ({active_keys: updated_active_keys}));
        this.componentDidMount();
      }
    });
  }

  setEventKey(eventKey) {
    var active_keys = this.state.active_keys;
    if (active_keys.includes(eventKey)) {
      active_keys = active_keys.filter(key => key !== eventKey);
    } else {
      active_keys.push(eventKey);
    }
    if (active_keys.length === 0) {
      this.props.setExpandAll(false);
    }
    if (active_keys.length === this.state.saved_filter_collections.length) {
      this.props.setExpandAll(true);
    }

    this.setState(state => ({active_keys: active_keys}));
  }

  render() {
    return (
      <div>
        <Accordion activeKey={this.state.active_keys} alwaysOpen>
          {this.state.saved_filter_collections.map(
            (saved_filter_collection, idx) => (
              <Accordion.Item eventKey={idx}>
                <Accordion.Header onClick={() => this.setEventKey(idx)}>
                  <h4>{saved_filter_collection.description}</h4>
                </Accordion.Header>
                <Accordion.Body>
                  <Row>
                    <Col style={{textAlign: 'right'}}>
                      <DeleteIcon
                        md={'auto'}
                        style={{textAlign: 'right'}}
                        onClick={() =>
                          this.handleDeleteClick(
                            idx,
                            saved_filter_collection.id
                          )
                        }
                      />
                    </Col>
                  </Row>
                  <ScrollField
                    filters={saved_filter_collection.filters}
                    query={saved_filter_collection.query}
                    selected_tab={'all'}
                    setLogout={this.props.setLogout}
                    logged_in={this.props.logged_in}
                    setSearchQuery={x => x}
                    setCategoryFilter={x => x}
                    setAffiliationFilter={x => x}
                  />
                </Accordion.Body>
              </Accordion.Item>
            )
          )}
        </Accordion>
      </div>
    );
  }
}

class LoadingSpinner extends React.Component {
  render() {
    return (
      <Container>
        <br></br>
        <Row>
          <Col style={{textAlign: 'center'}}>
            <div>
              {' '}
              <Spinner animation='border' />
            </div>
          </Col>
        </Row>
      </Container>
    );
  }
}

class ScrollField extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      items: [],
      hasMore: true,
      logged_in: this.props.logged_in,
    };
  }

  componentDidMount() {
    this.fetchPapers(0);
  }

  fetchPapers = offset => {
    var queryParams = '&time=' + this.props.filters.time;

    queryParams += '&tab=' + this.props.selected_tab;

    if (this.props.query.value.length !== 0) {
      queryParams += '&query=' + this.props.query.value;
      queryParams += '&query_type=' + this.props.query.type;
    }

    if (this.props.filters.affiliations.length !== 0) {
      queryParams += '&affiliations=' + this.props.filters.affiliations;
    }

    if (this.props.filters.categories.length !== 0) {
      queryParams += '&categories=' + this.props.filters.categories;
    }

    fetch('/api/papers?offset=' + offset + queryParams)
      .then(response => response.json())
      .then(result => {
        this.setState(state => ({
          items: state.items.concat(result.papers),
          hasMore: result.papers.length !== 0,
        }));
      });
  };

  componentDidUpdate(prevProps) {
    if (
      this.props.filters !== prevProps.filters ||
      this.props.query !== prevProps.query ||
      this.props.selected_tab !== prevProps.selected_tab
    ) {
      this.setState(state => ({items: []}));
      this.fetchPapers(0);
    }
  }

  fetchMoreData = () => {
    this.fetchPapers(this.state.items.length);
  };

  render() {
    const {items, hasMore} = this.state;
    return (
      <MathJax.Context
        input='ascii'
        onError={(MathJax, error) => {
          console.warn(error);
          console.log('Encountered a MathJax error, re-attempting a typeset!');
          MathJax.Hub.Queue(MathJax.Hub.Typeset());
        }}
        script='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.2/MathJax.js?config=AM_HTMLorMML'
        options={{
          asciimath2jax: {
            useMathMLspacing: true,
            delimiters: [['$', '$']],
            preview: 'none',
          },
        }}
      >
        <InfiniteScroll
          dataLength={items.length}
          next={this.fetchMoreData}
          hasMore={hasMore}
          loader={<LoadingSpinner></LoadingSpinner>}
        >
          {items.map(paper => (
            <Paper
              id={paper.id}
              created={paper.created}
              title={paper.title}
              abstract={paper.abstract}
              authors={paper.authors}
              doi={paper.doi}
              journal_ref={paper.journal_ref}
              primary_category={paper.primary_category}
              categories={paper.categories}
              affiliations={paper.affiliations}
              favorite={paper.favorite}
              setLogout={this.props.setLogout}
              logged_in={this.props.logged_in}
              setSearchQuery={value => this.props.setSearchQuery(value)}
              setCategoryFilter={value => this.props.setCategoryFilter(value)}
              setAffiliationFilter={value =>
                this.props.setAffiliationFilter(value)
              }
            ></Paper>
          ))}
        </InfiniteScroll>
      </MathJax.Context>
    );
  }
}

class SearchBar extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      value: '',
      type: 'full_text',
      label: 'Full-text',
    };
  }

  componentDidUpdate(prevProps) {
    if (this.props.query !== prevProps.query) {
      const type_to_label = {author: 'Author', full_text: 'Full-text'};
      this.setState(state => ({
        value: this.props.query.value,
        type: this.props.query.type,
        label: type_to_label[this.props.query.type],
      }));
    }
  }

  handleChangeValue(value) {
    const value_new = value;
    this.setState(state => ({value: value_new}));
  }

  handleClear() {
    const value_new = '';
    this.setState(state => ({value: value_new}));
    this.props.setSearchQuery(value_new);
  }

  handleKeyPress(event) {
    if (event.charCode === 13) {
      this.props.setSearchQuery({
        value: this.state.value,
        type: this.state.type,
      });
    }
  }

  handleTypeChange(option) {
    const new_option = option;
    this.setState(state => ({
      type: new_option.value,
      label: new_option.label,
    }));
  }

  render() {
    return (
      <InputGroup className='mb-5 mt-5'>
        <InputGroup.Text>
          <SearchIcon />
        </InputGroup.Text>
        <FormControl
          type='search'
          value={this.state.value}
          onChange={e => this.handleChangeValue(e.target.value)}
          onKeyPress={e => this.handleKeyPress(e)}
        ></FormControl>
        <div style={{width: '120px'}}>
          <Select
            value={{type: this.state.type, label: this.state.label}}
            defaultValue={{value: 'full_text', label: 'Full-text'}}
            options={[
              {value: 'full_text', label: 'Full-text'},
              {value: 'author', label: 'Author'},
            ]}
            onChange={option => this.handleTypeChange(option)}
          />
        </div>
      </InputGroup>
    );
  }
}

export default MainPage;
