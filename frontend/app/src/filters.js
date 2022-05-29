import React, {useEffect} from 'react';
import Select from 'react-select';
import Modal from 'react-bootstrap/Modal';
import FormControl from 'react-bootstrap/FormControl';
import Button from 'react-bootstrap/Button';
import Accordion from 'react-bootstrap/Accordion';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Tab from 'react-bootstrap/Tab';
import CardGroup from 'react-bootstrap/CardGroup';
import FilterListIcon from '@material-ui/icons/FilterList';
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore';
import UnfoldLessIcon from '@mui/icons-material/UnfoldLess';
import SaveIcon from '@mui/icons-material/Save';
import Tabs from 'react-bootstrap/Tabs';
import {useAccordionButton} from 'react-bootstrap/AccordionButton';
import Card from 'react-bootstrap/Card';

class Filters extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      event_key: null,
    };
  }

  render() {
    return (
      <Accordion defaultActiveKey='favorites'>
        <Row>
          <Col>
            <Tabs
              activeKey={this.props.selected_tab}
              onSelect={key => this.props.setSelectedTab(key)}
            >
              <Tab eventKey='all' title='all'></Tab>
              <Tab
                eventKey='favorites'
                title='favorites'
                disabled={!this.props.logged_in}
              ></Tab>
              <Tab
                eventKey='custom'
                title='custom'
                disabled={!this.props.logged_in}
              ></Tab>
            </Tabs>
          </Col>
          <Col md='auto'>
            <CustomToggle
              setEventKey={value => this.setEventKey(value)}
              expand_all={this.props.expand_all}
              flipExpandAll={this.props.flipExpandAll}
              selected_tab={this.props.selected_tab}
              style={{
                border: 'none',
                background: 'transparent',
                float: 'right',
              }}
            ></CustomToggle>
          </Col>
        </Row>
        <Accordion.Collapse eventKey='toggle_filters'>
          <Card.Body>
            <CardGroup>
              <Card>
                <Card.Body>
                  <Card.Title>Time</Card.Title>
                  <TimeFilter
                    setTimeFilter={value => this.props.setTimeFilter(value)}
                    time_filter={this.props.filters.time}
                  />
                </Card.Body>
              </Card>
              <Card>
                <Card.Body>
                  <Card.Title>Categories</Card.Title>
                  <CategoryFilter
                    setCategoryFilter={value =>
                      this.props.setCategoryFilter(value)
                    }
                    selected_categories={this.props.filters.categories}
                    available_categories={this.props.available_categories}
                  />
                </Card.Body>
              </Card>
              <Card>
                <Card.Body>
                  <Card.Title>Affiliation</Card.Title>
                  <AffiliationFilter
                    setAffiliationFilter={value =>
                      this.props.setAffiliationFilter(value)
                    }
                    selected_affiliations={this.props.filters.affiliations}
                    available_affiliations={this.props.available_affiliations}
                  />
                </Card.Body>
              </Card>
            </CardGroup>
            <Row>
              <Col style={{textAlign: 'right'}}>
                <div style={{lineHeight: 0.8}}>
                  <br></br>
                </div>
                <SaveQueryButton
                  logged_in={this.props.logged_in}
                  handleSaveClick={description =>
                    this.props.handleSaveClick(description)
                  }
                ></SaveQueryButton>
              </Col>
            </Row>
          </Card.Body>
        </Accordion.Collapse>
      </Accordion>
    );
  }
}

function CustomToggle({selected_tab, flipExpandAll, expand_all}) {
  const decoratedOnClick = useAccordionButton('toggle_filters');
  const deactivateAccordion = useAccordionButton(null);

  useEffect(() => {
    if (selected_tab === 'custom') {
      deactivateAccordion();
    }
  });
  if (selected_tab === 'custom') {
    if (expand_all) {
      return <UnfoldLessIcon fontSize='large' onClick={flipExpandAll} />;
    } else {
      return <UnfoldMoreIcon fontSize='large' onClick={flipExpandAll} />;
    }
  } else {
    return <FilterListIcon fontSize='large' onClick={decoratedOnClick} />;
  }
}

class AffiliationFilter extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      menuIsOpen: false,
    };
  }

  handleChange = selected_options => {
    const actual_options = selected_options
      .filter(option => option.value !== 'select_all')
      .map(option => option.value);

    if (actual_options.length < selected_options.length) {
      this.props.setAffiliationFilter(this.props.available_affiliations);
      this.setState({menuIsOpen: false});
    } else {
      this.props.setAffiliationFilter(actual_options);
    }
  };

  handleSelectAll = () => {
    this.props.setAffiliationFilter(this.props.available_affiliations);
  };

  handleMenuOpen = () => {
    if (this.state.menuIsOpen !== undefined) {
      this.setState({menuIsOpen: undefined});
    }
  };

  render() {
    return (
      <Select
        closeMenuOnSelect={false}
        isMulti
        menuIsOpen={this.state.menuIsOpen}
        value={this.props.selected_affiliations.map(organization => ({
          value: organization,
          label: organization,
        }))}
        onChange={selected_options => this.handleChange(selected_options)}
        onMenuOpen={this.handleMenuOpen}
        options={[{value: 'select_all', label: 'Select All '}].concat(
          this.props.available_affiliations.map(organization => ({
            value: organization,
            label: organization,
          }))
        )}
      />
    );
  }
}

class TimeFilter extends React.Component {
  render() {
    return (
      <Select
        options={[
          {value: 'last_day', label: 'Last Day'},
          {value: 'last_three_days', label: 'Last 3 Days'},
          {value: 'last_week', label: 'Last Week'},
          {value: 'last_four_weeks', label: 'Last 4 Weeks'},
          {value: 'last_six_months', label: 'Last 6 Months'},
          {value: 'last_year', label: 'Last Year'},
          {value: 'all_time', label: 'All Time'},
        ]}
        defaultValue={{value: 'last_day', label: 'Last Day'}}
        onChange={option => this.props.setTimeFilter(option.value)}
      />
    );
  }
}

class CategoryFilter extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      menuIsOpen: false,
    };
  }

  handleChange = selected_options => {
    const actual_options = selected_options
      .filter(option => option.value !== 'select_all')
      .map(option => option.value);

    if (actual_options.length < selected_options.length) {
      this.props.setCategoryFilter(this.props.available_categories);
      this.setState({menuIsOpen: false});
    } else {
      this.props.setCategoryFilter(actual_options);
    }
  };

  handleSelectAll = () => {
    this.props.setCategoryFilter(this.props.available_categories);
  };

  handleMenuOpen = () => {
    if (this.state.menuIsOpen !== undefined) {
      this.setState({menuIsOpen: undefined});
    }
  };

  render() {
    return (
      <Select
        closeMenuOnSelect={false}
        isMulti
        menuIsOpen={this.state.menuIsOpen}
        value={this.props.selected_categories.map(category => ({
          value: category,
          label: category,
        }))}
        onChange={selected_options => this.handleChange(selected_options)}
        onMenuOpen={this.handleMenuOpen}
        options={[{value: 'select_all', label: 'Select All '}].concat(
          this.props.available_categories.map(category => ({
            value: category,
            label: category,
          }))
        )}
      />
    );
  }
}

class SaveQueryButton extends React.Component {
  state = {isOpen: false, description: ''};

  handleOpenModal = () => this.setState({isOpen: true});
  handleCloseModal = () => this.setState({isOpen: false});
  handleSave = () => {
    this.setState({isOpen: false});
    this.props.handleSaveClick(this.state.description);
  };

  handleChange(value) {
    const value_new = value;
    this.setState(state => ({description: value_new}));
  }

  render() {
    if (this.props.logged_in) {
      return (
        <>
          <SaveIcon fontSize='large' onClick={() => this.handleOpenModal()} />
          <Modal show={this.state.isOpen} onHide={this.handleClose}>
            <Modal.Header>
              <Modal.Title>Enter query description</Modal.Title>
            </Modal.Header>
            <Modal.Body>
              <FormControl
                type='search'
                value={this.state.value}
                onChange={e => this.handleChange(e.target.value)}
              ></FormControl>
            </Modal.Body>

            <Modal.Footer>
              <Button variant='secondary' onClick={this.handleCloseModal}>
                Close
              </Button>
              <Button variant='primary' onClick={this.handleSave}>
                Save Query
              </Button>
            </Modal.Footer>
          </Modal>
        </>
      );
    } else {
      return null;
    }
  }
}

export default Filters;
